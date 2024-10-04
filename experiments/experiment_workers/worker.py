from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Lock, Process
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

REDIS_IP = os.environ.get('REDIS_IP', 'localhost')

app = celery.Celery(
    'worker',
    backend=f'redis://{REDIS_IP}:6379/1',
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


def get_onts(n_ports: int, autofind: bool = False):
    onts = []
    with ThreadPoolExecutor() as executor:
        results = executor.map(get_onts_by_port, range(n_ports))
    onts = [ont for result in results for ont in result]
    logging.info(len(onts))
    if autofind:
        autofind_onts = get_autofind_onts()
        logging.info(len(autofind_onts))
        onts.extend(autofind_onts)
    return onts


def get_autofind_onts():
    onts = []
    with ConnectHandler(**credentials) as conn:
        conn.enable()
        conn.config_mode()
        output = conn.send_command("display ont autofind all")
        parsed_output = parse_output(
            platform='huawei_smartax',
            command='display ont autofind all',
            data=output
        )
        for ont in parsed_output:
            onts.append({
                "fsp": ont["fsp"],
                "sn": ont["serial_number"].split(" ")[0],
                "gem": [],
                "vlan": [],
                "snmp": [],
                "registered": False
            })
    return onts


def get_onts_by_port(port: int):
    results = []
    with ConnectHandler(**credentials) as conn:
        conn.enable()
        print("Looking for onts in port", port)
        conn.send_command("config", auto_find_prompt=False)
        conn.find_prompt()
        conn.send_command("interface gpon 0/0", auto_find_prompt=False)
        conn.find_prompt()
        output = conn.send_command(f"display ont info {port}")
        parsed_output = parse_output(
            platform='huawei_smartax',
            command=f"display ont info {port}",
            data=output
        )
        raw_output = conn.send_command(f"display ont optical-info {port} all")
        optical_output = parse_output(
            platform='huawei_smartax',
            command=f"display ont optical-info {port} all",
            data=raw_output
        )
        for ont in parsed_output:
            print("Looking for ont in port", port)
            time.sleep(0.01)
            raw_output = conn.send_command(
                f"display ont gemport {port} ontid {ont['ont_id']}"
            )
            gem_output = parse_output(
                platform='huawei_smartax',
                command=f"display ont gemport {port} ontid {ont['ont_id']}",
                data=raw_output
            )
            vlan_output = []
            time.sleep(0.01)
            for j in range(1, 5):
                raw_output = conn.send_command(
                    f"display ont port vlan {port} {ont['ont_id']} byport eth {j}" # noqa
                )
                vlan_output += parse_output(
                    platform='huawei_smartax',
                    command=f"display ont port vlan {port} {ont['ont_id']} byport eth {j}", # noqa
                    data=raw_output
                )
            time.sleep(0.01)
            raw_output = conn.send_command(
                f"display ont snmp-profile {port} all"
            )
            snmp_output = parse_output(
                platform='huawei_smartax',
                command=f"display ont snmp-profile {port} all",
                data=raw_output
            )
            snmp_output = next(
                (snmp for snmp in snmp_output
                    if snmp["ont_id"] == ont["ont_id"]),
                None
            )
            voltage = next(
                (item for item in optical_output
                 if item["ont_id"] == ont["ont_id"]),
                None)
            results.append({
                "fsp": f"0/0/{port}",
                "ont": ont["ont_id"],
                "sn": ont["serial_number"],
                "gem": gem_output,
                "vlan": vlan_output,
                "snmp": snmp_output,
                "registered": True,
                "voltage": voltage["voltage"]
            })
        conn.send_command("quit", auto_find_prompt=False)
        conn.find_prompt()
    return results


def get_boards_and_services():
    boards = None
    services = None
    with ConnectHandler(**credentials) as net_connect:
        output = net_connect.send_command("display board 0")
        parsed_output = parse_output(
            platform='huawei_smartax',
            command="display board 0",
            data=output
        )
        boards = parsed_output
        output = net_connect.send_command("display sysman service state")
        parsed_output = parse_output(
            platform='huawei_smartax',
            command="display sysman service state",
            data=output
        )
        services = parsed_output
    return boards, services


def get_all_info():
    info = {
        "boards": None,
        "services": None,
        "onts": None,
    }
    boards, services = get_boards_and_services()
    info["boards"] = boards
    info["services"] = services
    _, n_ports = [
        (board["slot_id"], GPON_BOARDS[board["boardname"]])
        for board in boards
        if board["boardname"] in GPON_BOARDS
    ][0]
    # onts = get_onts(2, autofind=False)
    onts = get_onts(n_ports, autofind=True)
    info["onts"] = onts
    # with open('info.json', 'w') as f:
    #     import json
    #     # info = json.load(f)
    #     json.dump(info, f)
    print("Notifying all info")
    return info


def monitoring_tasks():
    # with open('info.json', 'r') as f:
    #     import json
    #     info = json.load(f)
    notify_all_info.apply_async(
        # (os.getenv("QUEUE_NAME", 'site_1'), info),
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
    try:
        CHAOS_MONKEY_IP = os.environ.get('CHAOS_MONKEY_IP', 'localhost')
        QUEUE_NAME = os.getenv("QUEUE_NAME", 'site_1')
        requests.post(f"http://{CHAOS_MONKEY_IP}:3500/{QUEUE_NAME}/ready", timeout=2)
    except requests.exceptions.RequestException:
        pass
    while True:
        try:
            boards, services = get_boards_and_services()
            notify_boards_and_services.apply_async(
                (os.getenv("QUEUE_NAME", 'site_1'), boards, services),
                queue='master'
            )
            _, n_ports = [
                (board["slot_id"], GPON_BOARDS[board["boardname"]])
                for board in boards
                if board["boardname"] in GPON_BOARDS
            ][0]
            # onts = get_onts(2)
            onts = get_onts(n_ports)
            notify_onts.apply_async(
                (os.getenv("QUEUE_NAME", 'site_1'), onts),
                queue='master'
            )
        except KeyboardInterrupt:
            break
        except (Exception,):
            notify_olt.apply_async(
                (os.getenv("QUEUE_NAME", 'site_1'), "down"),
                queue="master"
            )
            wait_olt_ready()
            notify_olt.apply_async(
                (os.getenv("QUEUE_NAME", 'site_1'), "up"),
                queue="master"
            )


register_lock = Lock()


@app.task
def register_ont(fsp: str, sn: str):
    new_ont = {}
    with ConnectHandler(**credentials) as conn:
        conn.enable()
        conn.send_command("config", auto_find_prompt=False)
        conn.find_prompt()
        register_lock.acquire()
        parsed_output = conn.send_command(
            "display ont autofind all",
            use_textfsm=True
        )
        autofind_ont = next(
            (_ont for _ont in parsed_output
             if _ont["serial_number"].split()[0] == sn),
            None)
        if not autofind_ont:
            chassis, slot, port = fsp.split("/")
            parsed_output = conn.send_command(
                f"display ont info {chassis} {slot} {port}",
                use_textfsm=True
            )
            print(f"display ont info {chassis} {slot} {port}")
            prev_id = next(
                (_ont["ont_id"] for _ont in parsed_output
                 if _ont["serial_number"] == sn),
                None
            )
            print(prev_id)
            print(f"interface gpon {chassis}/{slot}")
            conn.send_command(
                f"interface gpon {chassis}/{slot}",
                auto_find_prompt=False
            )
            conn.find_prompt()
            print(f"ont delete {port} {prev_id}")
            conn.send_command(
                f"ont delete {port} {prev_id}"
            )
            print("display ont autofind {port}")
            parsed_output = conn.send_command(
                "display ont autofind {port}",
                use_textfsm=True
            )
            autofind_ont = next(
                (_ont for _ont in parsed_output
                 if _ont["serial_number"].split()[0] == sn),
                None)
            print(autofind_ont)
        else:
            chassis, slot, port = autofind_ont["fsp"].split("/")
            conn.send_command(
                f"interface gpon {chassis}/{slot}",
                auto_find_prompt=False
            )
            conn.find_prompt()
        parsed_output = conn.send_command(
            f"ont add {port} sn-auth {sn} omci ont-lineprofile-id 500 ont-srvprofile-id 500 desc {sn}", # noqa
            use_textfsm=True
        )
        print(parsed_output)
        if parsed_output[0]["success"] != '1':
            raise Exception("ONT not registered")
        register_lock.release()
        parsed_output = conn.send_command(
            f"display ont info {port}",
            use_textfsm=True
        )
        print(parsed_output)
        found_ont = next(
            (_ont for _ont in parsed_output
             if _ont["serial_number"] == sn),
            None)
        optical_output = conn.send_command(
            f"display ont optical-info {port} all",
            use_textfsm=True,
        )
        print(optical_output)
        voltage = next(
            (item for item in optical_output
             if item["ont_id"] == found_ont["ont_id"]),
            None)
        print(voltage)
        gem_output = conn.send_command(
            f"display ont gemport {port} ontid {found_ont['ont_id']}",
            use_textfsm=True,
        )
        print(gem_output)
        vlan_output = []
        for j in range(1, 5):
            vlan_output = conn.send_command(
                f"display ont port vlan {port} {found_ont['ont_id']} byport eth {j}", # noqa
                use_textfsm=True
            )
            print(vlan_output)
        snmp_output = conn.send_command(
            f"display ont snmp-profile {port} all",
            use_textfsm=True
        )
        print(snmp_output)
        snmp_output = next(
            (snmp for snmp in snmp_output
                if snmp["ont_id"] == found_ont["ont_id"]),
            None
        )
        new_ont = {
                "fsp": f"0/0/{port}",
                "ont": found_ont["ont_id"],
                "sn": found_ont["serial_number"],
                "gem": gem_output,
                "vlan": vlan_output,
                "snmp": snmp_output,
                "registered": True,
                "voltage": voltage["voltage"]
            }
        conn.send_command("quit", auto_find_prompt=False)
        conn.find_prompt()
    return new_ont


@app.task
def fix_service(service: dict):
    update_service = service
    update_service['state'] = (
        'enable' if service['state'] == 'disable' else 'disable'
    )
    result = False
    with ConnectHandler(**credentials) as conn:
        conn.enable()
        conn.config_mode()
        conn.send_command(
            f"sysman service {update_service['network_service']} {update_service['state']}"  # noqa
        )
        output = conn.send_command("display sysman service state")
        parsed_output = parse_output(
            platform='huawei_smartax',
            command="display sysman service state",
            data=output
        )
        result = update_service in parsed_output
    return result


def wait_olt_ready():
    while True:
        try:
            with ConnectHandler(**credentials):
                break
        except KeyboardInterrupt:
            break
        except (Exception,):
            pass


if __name__ == '__main__':
    from master import (
        notify_all_info, notify_olt, notify_boards_and_services, notify_onts
    )
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
