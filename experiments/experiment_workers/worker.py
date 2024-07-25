from multiprocessing import Process
import os
import logging

from netmiko import ConnectHandler
from ntc_templates.parse import parse_output
import celery

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
    CELERY_LOG_LEVEL='DEBUG',
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
    with ConnectHandler(**credentials) as conn:
        output = conn.send_command("display board 0")
        parsed_output = parse_output(
             platform="huawei_smartax",
             command="display board 0",
             data=output
        )
        # print(parsed_output)
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
            # print(result)
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
            print(len(result))
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
        print(len(result))
        for ont in result:
            onts.append({
                "fsp": ont["fsp"],
                "sn": ont["serial_number"].split()[0],
                "registered": False
            })
    print(len(onts))
    return onts

def monitoring_onts():
    while True:
        try:
            notify_all_onts.apply_async(
                (os.getenv("QUEUE_NAME", 'celery'), get_all_onts()),
                queue='master',
                retry=True,
                retry_policy={
                    'max_retries': None,
                    'interval_start': 0,
                    'interval_step': 1,
                    'interval_max': 300,
                }
            )
            break
        except:
            pass
    while True:
        try:
            receive_onts_data.apply_async(
                (os.getenv("QUEUE_NAME", 'celery'), get_onts()),
                queue='master'
            )
        except:
            notify_olt_not_responding.apply_async(
                (os.getenv("QUEUE_NAME", 'celery'),),
                queue="master"
            )
            while True:
                try:
                    with ConnectHandler(**credentials) as conn:
                        notify_olt_up.apply_async(
                            (os.getenv("QUEUE_NAME", 'celery'),),
                            queue="master"
                        )
                        break
                except:
                    pass

@app.task
def register_ont(ont):
    try:
        with ConnectHandler(**credentials) as conn:
            conn.enable()
            conn.config_mode()
            output = conn.send_command("display ont autofind all")
            parsed_output = parse_output(platform='huawei_smartax', command='display ont autofind all', data=output)
            logging.info("Autofind ONTs")
            # print(parsed_output)
            for autofind_ont in parsed_output:
                print(f"Autofind ONT: {autofind_ont['serial_number']} - {ont}")
                if ont == autofind_ont["serial_number"].split()[0]:
                    print(f"ONT {autofind_ont} found in autofind")
                    chassis, slot, port = autofind_ont["fsp"].split("/")
                    interface_gpon = f"{chassis}/{slot}"
                    print(f"Registering ONT {ont} in interface {interface_gpon}")
                    conn.send_command(f"interface gpon {interface_gpon}", auto_find_prompt=False)
                    conn.find_prompt()
                    logging.info(f"entered interface {interface_gpon}")
                    output = conn.send_command(f"ont add {port} sn-auth {ont} omci ont-lineprofile-id 500 ont-srvprofile-id 500 desc {ont}")
                    parsed_output = parse_output(platform='huawei_smartax', command=f"ont add {interface_gpon[-1]} sn-auth {ont} omci ont-lineprofile-id 500 ont-srvprofile-id 500 desc {ont}", data=output)
                    print(parsed_output)
                    if parsed_output[0]["success"] != '1':
                        print("NO FUNCA")
                        return False
                    print("ONT registered")
                    output= conn.send_command(f"display ont info {port}")
                    print(output)
                    parsed_output = parse_output(platform='huawei_smartax', command=f"display ont info {port}", data=output)
                    print(parsed_output)
                    for _ont in parsed_output:
                        print(_ont['serial_number'])
                        if _ont["serial_number"] == ont:
                            return True
                    conn.send_command("quit", auto_find_prompt=False)
                    conn.find_prompt()
        return False
    except:
        return False

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

def prepare_olt():
    while True:
        try:
            with ConnectHandler(**credentials) as conn:
                break
        except:
            pass
    with ConnectHandler(**credentials) as conn:
        conn.enable()
        conn.config_mode()
        conn.send_command("ont-srvprofile gpon profile-id 500 profile-name new_link", auto_find_prompt=False)
        conn.find_prompt()
        conn.send_command("ont-port pots 4 eth 4")
        output = conn.send_command("port vlan eth1 500")
        parsed_output = parse_output(platform="huawei_smartax", command="port vlan eth1 500", data=output)
        if int(parsed_output[0]["failed"]) != 0:
            raise Exception("Failed to set port vlan")
        conn.send_command("commit")
        conn.send_command("quit", auto_find_prompt=False)
        conn.find_prompt()
        conn.send_command("ont-lineprofile gpon profile-id 500 profile-name new_link", auto_find_prompt=False)
        conn.find_prompt()
        conn.send_command("tcont 4 dba-profile-id 5")
        conn.send_command("gem add 126 eth tcont 4")
        conn.send_command("gem mapping 126 0 vlan 500")
        conn.send_command("commit")
        conn.send_command("quit", auto_find_prompt=False)
        conn.find_prompt()
    print("OLT Ready!")

if __name__ == '__main__':
    from master import receive_onts_data, notify_olt_not_responding, notify_all_onts, notify_olt_up
    prepare_olt()
    monitoring_thread = Process(target=monitoring_onts, daemon=True)
    monitoring_thread.start()
    logging.info(os.getenv('QUEUE_NAME', 'celery'))
    worker = app.Worker(
        include=['worker'],
        loglevel='INFO',
        hostname=os.getenv('HOSTNAME', 'worker'),
        queues=[os.getenv('QUEUE_NAME', 'celery')]
    )
    worker.start()
    logging.info('Worker started')
    monitoring_thread.join()
    

