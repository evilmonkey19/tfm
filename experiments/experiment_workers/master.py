import copy
from dataclasses import dataclass
import os
import sys
import time
from datetime import datetime
from threading import Lock, Event
import subprocess
import threading
import uuid

import celery
import yaml

from worker import register_ont, fix_service

RABBITMQ_IP = os.environ.get('RABBITMQ_IP', 'localhost')

print(f'Connecting to RabbitMQ at {RABBITMQ_IP}')

app = celery.Celery(
    'master',
    backend='redis://localhost:6379/1',
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
    worker_pool='solo',
)


@dataclass
class FixObject:
    uuid = uuid.uuid4()
    site: str
    is_ont: bool
    error_type: str
    ont_or_service: dict
    result = None

general_lock = Lock()
original_all_info = dict()
all_info = dict()
events = list()
to_fix = list()
olt_down = Event()

end_thread = Event()


def register_event(site = None, event = None, fix = None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S_%f")[:-3]
    if site is not None and event is not None:
        events.append(f"{timestamp},,{site},error,{event}")
        return
    if fix.result is None:
        events.append(f"{timestamp},{fix.uuid},{fix.site},detected,{fix.error_type}")
        return
    events.append(f"{timestamp},{fix.uuid},{fix.site},fixed,{fix.error_type}")

def add_to_fix(site, ont_or_service, error_type):
    is_ont = "ont_id" in ont_or_service
    fix = FixObject(
        site=site,
        is_ont=is_ont,
        error_type=error_type,
        ont_or_service=ont_or_service
    )
    with general_lock:
        if any(fix.site == f.site and fix.ont_or_service == f.ont_or_service for f in to_fix):
            return
        to_fix.append(fix)
        register_event(fix=fix)

def fixer():
    while not end_thread.is_set():
        time.sleep(1)
        with general_lock:
            print(to_fix)
            for fix in to_fix:
                if fix.result is not None:
                    if fix.result.ready():
                        print(f"Fixing {fix.error_type} in site {fix.site} finished")
                        if fix.is_ont:
                            print([all_info[fix.site]["onts"] for ont in all_info[fix.site]["onts"] if ont["fsp"] == fix.ont_or_service["fsp"]])
                        else:
                            register_event(fix=fix)
                        to_fix.remove(fix)
                elif fix.is_ont:
                    print("HOLAAAAAAA")
                    # register_ont.apply_async(args=(fix.site, fix.ont_or_service["ont_id"]), queue=fix.site)
                elif not fix.is_ont:
                    fix.result = fix_service.apply_async(
                        args=(fix.ont_or_service,),
                        queue=fix.site
                    )
                    print(f"Fixing service {fix.ont_or_service['network_service']} in site {fix.site}: {fix.uuid}")

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
    with general_lock:
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
    register_event(site=queue, event=f"OLT is {status}")
    if status == "down":
        olt_down.set()
    else:
        olt_down.clear()
        with general_lock:
            all_info[queue] = original_all_info[queue]

@app.task
def notify_boards_and_services(queue, boards: list, services: list):
    if not boards == all_info[queue]["boards"]:
        register_event(site=queue, event=f"Boards: board 4 is {boards[4]['status']}")
        all_info[queue]["boards"] = boards

    if not services == original_all_info[queue]["services"]:
        changed_service = next((s for s in services for s2 in all_info[queue]["services"] 
                                 if s["network_service"] == s2["network_service"] and s["state"] != s2["state"]), None)
        add_to_fix(queue, changed_service, "service changed")

def move_onts(queue, sn: str):
    onts: list = all_info[queue]["onts"]
    ont = next((ont for ont in onts if ont["sn"] == sn), None)
    onts.remove(ont)
    onts = [_ont for _ont in onts if ont["fsp"] == _ont["fsp"] and _ont["ont"] > ont["ont"]]
    for ont in onts:
        ont["ont"] -= 1



@app.task
def notify_onts(queue, onts: list):
    # _onts = copy.deepcopy(onts)
    # _onts = [{k: v for k, v in ont.items() if k != "voltage"} for ont in _onts]
    # if _onts == all_info[queue]["onts"]:
    #     return
    print("ONTS", onts)
    if len(onts) != len(all_info[queue]["onts"]) or \
        not all(v for ont in onts for v in ont.values()):
        all_info_sn = [ont["sn"] for ont in all_info[queue]["onts"]]
        onts_sn = [ont["sn"] for ont in onts]
        sn = next((sn for sn in onts_sn if sn not in all_info_sn), None)
        if sn is not None:
            ont = next((ont for ont in all_info[queue]["onts"] if ont["sn"] == sn), None)
            move_onts(queue, sn)
            add_to_fix(queue, ont, "unregistered")

    return
    for ont in onts:
        all_info_ont = next((_ont for _ont in all_info[queue]["onts"] if _ont["sn"] == ont["sn"]), None)
        ont_index = all_info[queue]["onts"].index(all_info_ont)
        print(ont)
            
        # Voltage
        if ont["voltage"] != all_info_ont["voltage"]:
            voltage_value = float(ont["voltage"])
            print(voltage_value)
            if 3.6 < voltage_value < 3.8:
                register_event(site=queue, event=f"ONT {ont['sn']} has high voltage")
            elif 2.8 < voltage_value < 3.0:
                register_event(site=queue, event=f"ONT {ont['sn']} has low voltage")
            elif 3.2 < voltage_value < 3.4:
                register_event(site=queue, event=f"ONT {ont['sn']} has normal voltage")
            all_info[queue]["onts"][ont_index] = ont
        
        original_ont = next((ont for ont in all_info[queue]["onts"] if ont["ont_id"] == ont["ont_id"]), None)
        if original_ont is None:
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