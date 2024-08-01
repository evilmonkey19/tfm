from multiprocessing import Process
import os
import logging
import time

from netmiko import ConnectHandler
from ntc_templates.parse import parse_output
import celery
import requests

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

def get_all_info():
    info = {
        "boards" : None,
        "services": None,
        "onts": [],
    }
    with ConnectHandler(**credentials) as conn:
        conn.enable()
        output = conn.send_command("display sysman service state")
        parsed_output = parse_output(
                platform="huawei_smartax",
                command="display sysman service state",
                data=output
            )
        info["services"] = parsed_output
        output = conn.send_command("display board 0")
        parsed_output = parse_output(
             platform="huawei_smartax",
             command="display board 0",
             data=output
        )
        info['boards'] = parsed_output
        _, n_ports = [(board["slot_id"], GPON_BOARDS[board["boardname"]])
                                for board in parsed_output
                                if board["boardname"] in GPON_BOARDS][0]
        conn.config_mode()
        conn.send_command("interface gpon 0/0", auto_find_prompt=False)
        conn.find_prompt()
        for i in range(n_ports):
            command = f"display ont info {i}"
            output = conn.send_command(command)
            result = parse_output(
                 platform="huawei_smartax",
                 command=command,
                 data=output
                )
            for ont in result:
                time.sleep(0.01)
                raw_output = conn.send_command(f"display ont gemport {i} ontid {ont['ont_id']}")
                gem_output = parse_output(
                        platform="huawei_smartax",
                        command=f"display ont gemport {i} ontid {ont['ont_id']}",
                        data=raw_output
                )
                vlan_output = []
                time.sleep(0.01)
                for j in range(1,5):
                    raw_output = conn.send_command(f"display ont port vlan {i} {ont['ont_id']} byport eth {j}")
                    vlan_output += parse_output(
                        platform="huawei_smartax",
                        command=f"display ont port vlan {i} {ont['ont_id']} byport eth {j}",
                        data=raw_output
                    )
                time.sleep(0.01)
                raw_output = conn.send_command(f"display ont snmp-profile {i} all")
                snmp_output = parse_output(
                        platform="huawei_smartax",
                        command=f"display ont snmp-profile {i} all",
                        data=raw_output
                )
                info['onts'].append({
                    "fsp": f"0/0/{i}",
                    "ont": ont["ont_id"],
                    "sn": ont["serial_number"],
                    "gem": gem_output,
                    "vlan": vlan_output,
                    "snmp": snmp_output,
                    "registered": True
                })

        command = "display ont autofind all"
        output = conn.send_command(command)
        result = parse_output(
             platform="huawei_smartax",
             command=command,
             data=output
        )
        for ont in result:
            info["onts"].append({
                "fsp": ont["fsp"],
                "sn": ont["serial_number"].split()[0],
                "registered": False
            })
    return info

def monitoring_tasks():
    notify_all_info.apply_async(
        (os.getenv("QUEUE_NAME", 'site_1'), get_all_info()),
        queue='master',
        retry=True,
        retry_policy={
            'max_retries': None,
            'interval_start': 0,
            'interval_step': 1,
            'interval_max': 300,
        }
    )
    requests.post("http://localhost:3500/site_1/ready", timeout=20)
    while True:
        try:
            info = get_boards_and_services()
            notify_boards_and_services.apply_async(
                (os.getenv("QUEUE_NAME", 'site_1'), info),
                queue='master'
            )
            # info["boards"][0]["boardname"]
            # 4 workers
            # notify_onts_by_port.apply_async(
            #     (os.getenv("QUEUE_NAME", 'site_1'), get_onts()),
            #     queue='master'
            # )
        except KeyboardInterrupt:
            break
        except:
            notify_olt.apply_async(
                (os.getenv("QUEUE_NAME", 'site_1'),"down"),
                queue="master"
            )
            wait_olt_ready()
            notify_olt.apply_async(
                (os.getenv("QUEUE_NAME", 'site_1'),"up"),
                queue="master"
            )

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
    except Exception:
        return False


@app.task
def get_boards_and_services():
    info = {
        "boards": None,
        "services": None
    }
    with ConnectHandler(**credentials) as net_connect:
        output = net_connect.send_command("display board 0")
        parsed_output = parse_output(
            platform='huawei_smartax',
            command="display board 0",
            data=output
        )
        info["boards"] = parsed_output
        output = net_connect.send_command("display sysman service state")
        parsed_output = parse_output(
            platform='huawei_smartax',
            command="display sysman service state",
            data=output
        )
        info["services"] = parsed_output
    return info

def wait_olt_ready():
    while True:
        try:
            with ConnectHandler(**credentials):
                break
        except KeyboardInterrupt:
            break
        except:
            pass


if __name__ == '__main__':
    from master import notify_all_info, notify_olt, notify_boards_and_services
    wait_olt_ready()
    monitoring_thread = Process(target=monitoring_tasks, daemon=True)
    monitoring_thread.start()
    logging.info(os.getenv('QUEUE_NAME', 'site_1'))
    worker = app.Worker(
        include=['worker'],
        loglevel='INFO',
        hostname=os.getenv('HOSTNAME', 'worker_site_1'),
        queues=[os.getenv('QUEUE_NAME', 'site_1')]
    )
    worker.start()
    logging.info('Worker started')
    monitoring_thread.join()
    

