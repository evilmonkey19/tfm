import os
import time
from datetime import datetime
from multiprocessing import Queue, Lock, Manager, Process, Value, Event

import celery
import yaml
import subprocess

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
serviceLock = manag.Lock()
registered_network_onts = manag.dict()

onts_queue = Queue()

olt_down = Event()

stop_reregistering = Value('b', False)

onts_lock = Lock()

def reregister_onts():
    onts = []
    registered_onts = []
    results = []
    while True:
        if olt_down.is_set():
            onts = []
            registered_onts = []
            results = []
        if bool(stop_reregistering.value) is True:
            break
        if not onts_queue.empty() or results != []:
            registered_onts = [ont for ont in registered_onts if time.time() - ont[1] < 30]
            with onts_lock:
                while not onts_queue.empty():
                    ont = onts_queue.get()
                    _registered_onts = [ont[0] for ont in registered_onts]
                    registering_onts = [result[1] for result in results]
                    if ont not in onts and ont not in _registered_onts and ont not in registering_onts:
                        onts.append(ont)
            if onts:
                ont = onts.pop(0)
                print(f"Sending task to", ont)
                result = register_ont.apply_async(args=(ont[1],), queue=ont[0])
                results.append((result, ont))
            try:
                _results = results.copy()
                for result in _results:
                    if result[0].ready():
                        with open('misconfigurations_results.csv', 'a') as f:
                            f.write(f"{result[1][0]},registered {result[1][1]},{datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]}\n")
                        print(f"ONT {result[1][1]} registered in OLT {result[1][0]}")
                        registered_onts.append((result[1], time.time()))
                        results.remove(result)
                    elif result[0].failed():
                        print(f"Failed to reregister ONT {result[1][1]} in OLT {result[1][0]}")
                        onts.append(result[1])
                        results.remove(result)
            except celery.exceptions.TimeoutError:
                print(f"Celery Timeout: Failed to reregister ONT {result[1][1]} in OLT {result[1][0]}")
                onts.append(result[1])
                results.remove(result)
                continue
            

@app.task
def notify_all_onts(site_name: str, onts: list):
    real_onts = []
    with open(f'{site_name}.yaml.j2', 'r') as f2:
        yaml_data = yaml.safe_load(f2)
        ports = yaml_data["frames"][0]["slots"][0]["ports"]
        real_onts = [
            {"sn": ont["sn"], "registered": ont["registered"]}
            for port in ports
            for ont in port
        ]
    correct_onts = [ont for ont in onts if ont['sn'] in [ont['sn'] for ont in real_onts]]
    row = {
        "site_name": site_name,
        "detected_onts": len(onts),
        "real_onts": len(real_onts),
        "correct_onts": len(correct_onts),
    }
    with open('results_detected_onts.csv', 'a') as f:
        f.write(f"{row['site_name']},{row['real_onts']},{row['detected_onts']},{row['correct_onts']}\n")
    
    registered_network_onts[site_name] = [ont["sn"] for ont in onts if ont["registered"]]

        
@app.task
def receive_onts_data(queue, data):
    if not registered_network_onts:
        return
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
    registered_onts = [ont["serial_number"] for port in data for ont in port]
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
    with open('misconfigurations_results.csv', 'a') as f:
        for ont in new_unregistered_onts:
            f.write(f"{queue},unregistered {ont[1]},{timestamp}\n")
    print(f"ONTs {new_unregistered_onts} are not registered in OLT {queue}")

@app.task
def notify_olt_not_responding(queue):
    detected_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
    with open("misconfigurations_results.csv", "a") as f:
        f.write(f"{queue},OLT not responding,{detected_time}\n")
    print(f"OLT {queue} is not responding")
    with onts_lock:
        while not onts_queue.empty():
            onts_queue.get()
    olt_down.set()

@app.task
def notify_olt_up(queue):
    detected_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
    with open("misconfigurations_results.csv", "a") as f:
        f.write(f"{queue},OLT up,{detected_time}\n")
    print(f"OLT {queue} is up")
    olt_down.clear()


if __name__ == '__main__':
    subprocess.run(["docker", "compose", "up", "-d", "--build"])
    task = Process(target=reregister_onts, name='reregister_onts', daemon=True)
    task.start()
    worker = app.Worker(
        include=['master'],
        loglevel='INFO',
        hostname=os.getenv('HOSTNAME', 'localhost'),
        queues=['celery', 'master'],
        time_limit=datetime.utcnow().timestamp() + 7200  # Set the time limit to 7200 seconds (2 hours) from current UTC time
    )
    worker.start()
    stop_reregistering = True
    task.join()
    subprocess.run(["docker", "compose", "down"])