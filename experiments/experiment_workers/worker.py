import time
import os
import threading
import logging

from netmiko import ConnectHandler
from ntc_templates.parse import parse_output
import celery

from master import receive_onts_data, notify_olt_not_responding, notify_all_onts

logging.basicConfig(level=logging.INFO)

RABBITMQ_IP = os.environ.get('RABBITMQ_IP', 'localhost')

print(f'Connecting to RabbitMQ at {RABBITMQ_IP}')

credentials = {
    'username': 'admin',
    'password': 'admin',
    'host': os.environ.get('HUAWEI_SMARTAX_IP', 'localhost'),
    'port': 9000,
    'device_type': 'huawei_smartax',
}

app = celery.Celery(
    'worker',
    backend=f'rpc://guest@{RABBITMQ_IP}//',
    broker=f'pyamqp://guest@{RABBITMQ_IP}//'
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

GPON_BOARDS: dict[str, int] = {
    'H901XGHDE': 8,
    'H901OGHK': 24,
    'H901NXED': 8,
    'H901OXHD': 8,
    'H902OXHD': 8,
    'H901GPSFE': 16,
    'H901OXEG': 24,
    'H901TWEDE': 8,
    'H901XSHF': 16,
    'H902GPHFE': 16,
}

def get_onts():
    results = []
    print("Connecting to the device")
    print(credentials)
    with ConnectHandler(**credentials) as conn:
        output = conn.send_command("display board 0")
        print(output)
        parsed_output = parse_output(
             platform="huawei_smartax",
             command="display board 0",
             data=output
        )
        print(parsed_output)
        slot_id, n_ports = [(board["slot_id"], GPON_BOARDS[board["boardname"]])
                                for board in parsed_output
                                if board["boardname"] in GPON_BOARDS][0]
        for i in range(n_ports):
            command = f"display ont info 0 {slot_id} {i}"
            print(command)
            output = conn.send_command(command)
            result = parse_output(
                 platform="huawei_smartax",
                 command=command,
                 data=output
                )
            results.append(result)
        return results

def get_all_onts():
    onts = []
    with ConnectHandler(**credentials) as conn:
        output = conn.send_command("display board 0")
        parsed_output = parse_output(
             platform="huawei_smartax",
             command="display board 0",
             data=output
        )
        slot_id, n_ports = [(board["slot_id"], GPON_BOARDS[board["boardname"]])
                                for board in parsed_output
                                if board["boardname"] in GPON_BOARDS][0]
        for i in range(n_ports):
            command = f"display ont info 0 {slot_id} {i}"
            output = conn.send_command(command)
            result = parse_output(
                 platform="huawei_smartax",
                 command=command,
                 data=output
                )
            for ont in result:
                onts.append({
                    "fsp": ont["fsp"],
                    "sn": ont["serial_number"],
                    "registered": True
                })

        conn.enable()
        conn.config_mode()
        command = "display ont autofind all"
        output = conn.send_command(command)
        result = parse_output(
             platform="huawei_smartax",
             command=command,
             data=output
        )
        for ont in result:
            onts.append({
                "fsp": ont["fsp"],
                "sn": ont["serial_number"].split()[0],
                "registered": False
            })
    return onts

def monitoring_onts():
    time.sleep(30)
    notify_all_onts.apply_async(
        (os.getenv("QUEUE_NAME", 'celery'), get_all_onts()),
        queue='master'
    )
    while True:
        try:
            receive_onts_data.apply_async(
                ({os.getenv("QUEUE_NAME", 'celery'): get_onts()}),
                queue='master'
            )
        except:
            notify_olt_not_responding.delay(
                (os.getenv("QUEUE_NAME", 'celery'),),
                queue="master"
            )
            time.sleep(1)

@app.task
def add(x, y):
    return x + y

@app.task
def get_gpon_board():
    COMMAND = 'display board 0'
    with ConnectHandler(**credentials) as net_connect:
        output = net_connect.send_command(COMMAND)
        parsed_output = parse_output(platform='huawei_smartax', command=COMMAND, data=output)
        return parsed_output
    
if __name__ == '__main__':
    monitoring_thread = threading.Thread(target=monitoring_onts)
    monitoring_thread.start()
    worker = app.Worker(
        include=['worker'],
        loglevel='INFO',
        hostname=os.getenv('HOSTNAME', 'worker'),
        queues=[os.getenv('QUEUE_NAME', 'celery')]
    )
    worker.start()
    logging.info('Worker started')
    monitoring_thread.join()
    

