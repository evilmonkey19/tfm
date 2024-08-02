import copy
from dataclasses import dataclass
import os
import sys
import time
from datetime import datetime
from multiprocessing import Manager
import subprocess
import threading

import celery
import yaml

from worker import register_ont, fix_service

RABBITMQ_IP = os.environ.get('RABBITMQ_IP', 'localhost')

print(f'Connecting to RabbitMQ at {RABBITMQ_IP}')

app = celery.Celery(
    'master',
    backend=f'rpc://guest@{RABBITMQ_IP}//',
    broker=f'pyamqp://guest@{RABBITMQ_IP}//',
)

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Madrid',
    enable_utc=True,
    broker_connection_retry=True,
    broker_connection_retry_on_startup=True,
)


@dataclass
class FixObject:
    site: str
    is_ont: bool
    error_type: str
    ont_or_service: dict
    result = None

manag = Manager()
original_all_info = manag.dict()
all_info = manag.dict()
events = manag.list()
to_fix = manag.list()
olt_down = manag.Event()

end_thread = threading.Event()




def register_event(site, event):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S_%f")[:-3]
    events.append(f"{site},{event},{timestamp}")

def add_to_fix(site, ont_or_service, error_type):
    is_ont = "ont_id" in ont_or_service
    fix = FixObject(site, is_ont, error_type, ont_or_service)
    if fix not in list(to_fix):
        to_fix.append(fix)

def fixer():
    while True:
        if end_thread.is_set():
            break
        if list(to_fix):
            # pylint: disable=consider-using-enumerate
            for i in range(len(to_fix)):
                fix = to_fix[i]
                if fix.result is not None:
                    print(f"Fixed {fix.result.status}")
                    if fix.result.ready():
                        if fix.result.failed():
                            register_event(fix.site, f"failed to fix {fix.ont_or_service} with problem {fix.error_type}")
                        else:
                            register_event(fix.site, f"fixed {fix.ont_or_service} with problem {fix.error_type}")
                        to_fix.pop(i)
                elif fix.is_ont:
                    # register_ont.apply_async(args=(fix_object.site, fix_object.ont_or_service["ont_id"]), queue=fix_object.site)
                    pass
                elif not fix.is_ont:
                    fix.result = fix_service.apply_async(
                        args=(fix.ont_or_service,),
                        queue=fix.site
                    )
                    to_fix[i] = fix  # Update the fix object in the list
                else:
                    continue
            time.sleep(1)


@app.task
def notify_all_info(site_name: str, info: dict):
    real_onts = []
    with open(f'{site_name}.yaml.j2', 'r') as f2:
        yaml_data = yaml.safe_load(f2)
        ports = yaml_data["frames"][0]["slots"][0]["ports"]
        real_onts = [
            {"sn": ont["sn"], "registered": ont["registered"]}
            for port in ports
            for ont in port
        ]
    correct_onts = [ont for ont in info["onts"] if ont['sn'] in [ont['sn'] for ont in real_onts]]
    row = {
        "site_name": site_name,
        "real_onts": len(real_onts),
        "detected_onts": len(info["onts"]),
        "correct_onts": len(correct_onts),
    }
    with open('results_detected_onts.csv', 'a') as f:
        f.write(f"{row['site_name']},{row['real_onts']},{row['detected_onts']},{row['correct_onts']}\n")
    
    
    info["onts"] = [ont for ont in info["onts"] if ont["registered"]]
    for ont in info["onts"]:
        del ont["voltage"]
    all_info[site_name] = info
    original_all_info[site_name] = info

# ### TO FIX ###
# @app.task
# def receive_onts_data(queue, data):
#     if not registered_network_onts:
#         return
#     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
#     registered_onts = [ont["serial_number"] for port in data for ont in port]
#     if queue not in registered_network_onts:
#         return
#     all_unregistered_onts = [ont for ont in registered_network_onts[queue] if ont not in registered_onts]
#     with onts_lock:
#         previous_unregistered_onts = []
#         while not onts_queue.empty():
#             previous_unregistered_onts.append(onts_queue.get())
#         print(f"Previous unregistered ONTs: {previous_unregistered_onts}")
#         print(f"All unregistered ONTs: {all_unregistered_onts}")
#         new_unregistered_onts = [(queue, ont) for ont in all_unregistered_onts if ont[1] not in previous_unregistered_onts]
#         print(f"New unregistered ONTs: {new_unregistered_onts}")
#         # print(f"Unregistered ONTs: {new_unregistered_onts}")
#         for ont in previous_unregistered_onts + new_unregistered_onts:
#             onts_queue.put(ont)
#     with open('events_log.csv', 'a') as f:
#         for ont in new_unregistered_onts:
#             f.write(f"{queue},unregistered {ont[1]},{timestamp}\n")
#     print(f"ONTs {new_unregistered_onts} are not registered in OLT {queue}")


##############################################
##                                          ##
##               TASKS                      ##
##                                          ##
##############################################

@app.task
def notify_olt(queue, status: str):
    register_event(queue, f"OLT is {status}")
    if status == "down":
        olt_down.set()
    else:
        olt_down.clear()
        all_info[queue] = original_all_info[queue]

@app.task
def notify_boards_and_services(queue, boards: list, services: list):
    if not boards == all_info[queue]["boards"]:
        register_event(queue, f"board 4 is {boards[4]['status']}")
        all_info[queue]["boards"] = boards
    if not services == all_info[queue]["services"]:
        print(all_info[queue]["services"])
        changed_service = None
        for service in services:
            for service2 in all_info[queue]["services"]:
                if service["network_service"] == service2["network_service"]:
                    if service["state"] != service2["state"]:
                        changed_service = service
                        break
        changed_service = next((service for service in services for service2 in all_info[queue]["services"] if service["state"] != service2["state"]), None)
        register_event(queue, f"service {changed_service} is {changed_service['state']}")
        all_info[queue]["services"] = services
        add_to_fix(queue, changed_service, "service changed")

@app.task
def notify_onts(queue, onts: list):
    _onts = copy.deepcopy(onts)
    _onts = [{k: v for k, v in ont.items() if k != "voltage"} for ont in _onts]
    if _onts == all_info[queue]["onts"]:
        return
    for ont in onts:
        original_ont = next((ont for ont in all_info[queue]["onts"] if ont["ont_id"] == ont["ont_id"]), None)
        if original_ont is None:
            register_event(queue, f"ONT {ont['ont_id']} is unregistered")
            add_to_fix(queue, ont, "unregistered")
            return
        if ont == original_ont:
            return
        # if ont


def timer(task, worker):
    time.sleep(5*60+30)
    worker.shutdown()
    task.join()

if __name__ == '__main__':
    worker = None
    if not sys.argv[1] == 'local':
        subprocess.run(["docker", "compose", "up", "-d", "--build"])
    task = threading.Thread(target=fixer, name='fixer', daemon=True)
    task.start()
    task = None
    worker = app.Worker(
        include=['master'],
        loglevel='INFO',
        hostname=os.getenv('HOSTNAME', 'localhost'),
        queues=['celery', 'master'],
        time_limit=datetime.utcnow().timestamp() + 7200  # Set the time limit to 7200 seconds (2 hours) from current UTC time
    )
    worker.start()
    if not sys.argv[1] == 'local':
        timer_thread = threading.Thread(target=timer, args=(worker, task), daemon=True)
        timer_thread.start()
    with open('events_log.csv', 'a') as f:
        for event in events:
            f.write(f"{event}\n")
    if not sys.argv[1] == 'local':
        subprocess.run(["docker", "compose", "down"])