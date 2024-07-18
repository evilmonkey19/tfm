import os
import threading
import celery
from datetime import datetime

import yaml

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


network_onts = {}

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
        "real_onts": len(real_onts),
        "detected_onts": len(onts),
        "correct_onts": len(correct_onts),
    }
    with open('results_detected_onts.csv', 'a') as f:
        f.write(f"{row['site_name']},{row['real_onts']},{row['detected_onts']},{row['correct_onts']}\n")

        
            

@app.task
def receive_onts_data(data):
    print(list(data.keys()))
    # print("#"*80)
    # print("Received data:")
    # # print(data)
    # print("#"*80)

@app.task
def notify_olt_not_responding(queue):
    print(f"OLT {queue} is not responding")

if __name__ == '__main__':
    # task_scheduler = threading.Thread(target=)
    # task_scheduler.start()
    worker = app.Worker(
        include=['master'],
        loglevel='INFO',
        hostname=os.getenv('HOSTNAME', 'localhost'),
        queues=['celery', 'master'],
        time_limit=datetime.utcnow().timestamp() + 7200  # Set the time limit to 7200 seconds (2 hours) from current UTC time
    )
    worker.start()