import os
import threading
import time
from datetime import datetime

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


registered_network_onts = {}

onts_with_misconfigurations = []


def reregister_onts():
    global onts_with_misconfigurations
    onts = onts_with_misconfigurations.copy()
    for ont in onts:
        print(ont[1], ont[0])
        if register_ont.apply_async((ont[1],), queue=ont[0]).get(disable_sync_subtasks=False):
            with open('misconfigurations_results.csv', 'a') as f:
                f.write(f"{ont[0]},registered {ont[1]},{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}\n")
            onts_with_misconfigurations.remove(ont)
        else:
            print(f"Failed to reregister ONT {ont[1]} in OLT {ont[0]}")


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
    global onts_with_misconfigurations
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    registered_onts = [ont["serial_number"] for port in data for ont in port]
    unregistered_onts = [ont for ont in registered_network_onts[queue] if ont not in registered_onts]
    new_unregistered_onts = [(queue, ont) for ont in unregistered_onts if (queue, ont) not in onts_with_misconfigurations]

    if new_unregistered_onts:
        onts_with_misconfigurations.extend(new_unregistered_onts)
        with open('misconfigurations_results.csv', 'a') as f:
            for ont in new_unregistered_onts:
                f.write(f"{queue},unregistered {ont[1]},{timestamp}\n")
        threading.Thread(target=reregister_onts, daemon=True).start()


@app.task
def notify_olt_not_responding(queue):
    detected_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    with open("misconfigurations_results.csv", "a") as f:
        f.write(f"{queue},OLT not responding,{detected_time}\n")
    print(f"OLT {queue} is not responding")


if __name__ == '__main__':
    subprocess.run(["docker", "compose", "up", "-d", "--build"])

    worker = app.Worker(
        include=['master'],
        loglevel='INFO',
        hostname=os.getenv('HOSTNAME', 'localhost'),
        queues=['celery', 'master'],
        time_limit=datetime.utcnow().timestamp() + 7200  # Set the time limit to 7200 seconds (2 hours) from current UTC time
    )
    worker.start()
    subprocess.run(["docker", "compose", "down"])