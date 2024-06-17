import time
import os

from netmiko import ConnectHandler
from ntc_templates.parse import parse_output
from celery import Celery

RABBITMQ_IP = os.environ.get('RABBITMQ_IP', 'localhost')

print(f'Connecting to RabbitMQ at {RABBITMQ_IP}')

app = Celery('tasks', backend=f'rpc://guest@{RABBITMQ_IP}//', broker=f'pyamqp://guest@{RABBITMQ_IP}//')

@app.task
def add(x, y):
    time.sleep(5)
    return x + y

@app.task
def get_gpon_board():
    credentials = {
        'username': 'admin',
        'password': 'admin',
        'host': os.environ.get('HUAWEI_SMARTAX_IP', 'localhost'),
        'port': 9000,
        'device_type': 'huawei_smartax',
    }
    COMMAND = 'display board 0'
    with ConnectHandler(**credentials) as net_connect:
        output = net_connect.send_command(COMMAND)
        parsed_output = parse_output(platform='huawei_smartax', command=COMMAND, data=output)
        return parsed_output