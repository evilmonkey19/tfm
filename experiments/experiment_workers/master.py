import os
import sys
import time
from datetime import datetime
from multiprocessing import Manager
import subprocess
import threading

import celery
import yaml

from worker import register_ont

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


manag = Manager()
original_all_info = manag.dict()
all_info = manag.dict()
events = manag.list()
to_fix = manag.list()
olt_down = manag.Event()

end_thread = threading.Event()

def fixer():
    while True:
        if end_thread.is_set():
            break


# def reregister_onts():
#     onts = []
#     registered_onts = []
#     results = []
#     while True:
#         if olt_down.is_set():
#             onts = []
#             registered_onts = []
#             results = []
#         if bool(stop_reregistering.value) is True:
#             break
#         if not onts_queue.empty() or results != []:
#             registered_onts = [ont for ont in registered_onts if time.time() - ont[1] < 30]
#             with onts_lock:
#                 while not onts_queue.empty():
#                     ont = onts_queue.get()
#                     _registered_onts = [ont[0] for ont in registered_onts]
#                     registering_onts = [result[1] for result in results]
#                     if ont not in onts and ont not in _registered_onts and ont not in registering_onts:
#                         onts.append(ont)
#             if onts:
#                 ont = onts.pop(0)
#                 result = register_ont.apply_async(args=(ont[1],), queue=ont[0])
#                 results.append((result, ont))
#             try:
#                 _results = results.copy()
#                 for result in _results:
#                     if result[0].ready():
#                         with open('events_log.csv', 'a') as f:
#                             f.write(f"{result[1][0]},registered {result[1][1]},{datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]}\n")
#                         print(f"ONT {result[1][1]} registered in OLT {result[1][0]}")
#                         registered_onts.append((result[1], time.time()))
#                         results.remove(result)
#                     elif result[0].failed():
#                         print(f"Failed to reregister ONT {result[1][1]} in OLT {result[1][0]}")
#                         onts.append(result[1])
#                         results.remove(result)
#             except celery.exceptions.TimeoutError:
#                 print(f"Celery Timeout: Failed to reregister ONT {result[1][1]} in OLT {result[1][0]}")
#                 onts.append(result[1])
#                 results.remove(result)
#                 continue
            

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
    
    all_info[site_name] = info
    original_all_info[site_name] = info

### TO FIX ###
@app.task
def receive_onts_data(queue, data):
    if not registered_network_onts:
        return
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
    registered_onts = [ont["serial_number"] for port in data for ont in port]
    if queue not in registered_network_onts:
        return
    all_unregistered_onts = [ont for ont in registered_network_onts[queue] if ont not in registered_onts]
    with onts_lock:
        previous_unregistered_onts = []
        while not onts_queue.empty():
            previous_unregistered_onts.append(onts_queue.get())
        print(f"Previous unregistered ONTs: {previous_unregistered_onts}")
        print(f"All unregistered ONTs: {all_unregistered_onts}")
        new_unregistered_onts = [(queue, ont) for ont in all_unregistered_onts if ont[1] not in previous_unregistered_onts]
        print(f"New unregistered ONTs: {new_unregistered_onts}")
        # print(f"Unregistered ONTs: {new_unregistered_onts}")
        for ont in previous_unregistered_onts + new_unregistered_onts:
            onts_queue.put(ont)
    with open('events_log.csv', 'a') as f:
        for ont in new_unregistered_onts:
            f.write(f"{queue},unregistered {ont[1]},{timestamp}\n")
    print(f"ONTs {new_unregistered_onts} are not registered in OLT {queue}")


##############################################
##                                          ##
##               TASKS                      ##
##                                          ##
##############################################

@app.task
def notify_olt(queue, status: str):
    detected_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
    if status == "down":
        olt_down.set()
    else:
        olt_down.clear()
        all_info[queue] = original_all_info[queue] 
    events.append(f"{queue},OLT {status},{detected_time}")

@app.task
def notify_boards_and_services(queue, info: dict):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
    if not info["boards"] == all_info[queue]["boards"]:
        events.append(f"{queue},board 4 is {info['boards'][4]['status']},{timestamp}")
        all_info[queue]["boards"] = info["boards"]
        print(f"Board 4 is {info['boards'][4]['status']}")
    if not info["services"] == all_info[queue]["services"]:
        changed_service = next(service for service in info["services"] if service["state"] != all_info[queue]["services"][service]["state"])
        events.append(f"{queue},service {changed_service} is {changed_service['state']},{timestamp}")
        all_info[queue]["services"] = info["services"]
        print(f"Service {info['services']} is {info['services']['state']}")

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