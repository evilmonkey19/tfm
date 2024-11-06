from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Lock, Process
import os
import logging
import time
import argparse

from netmiko import ConnectHandler
from ntc_templates.parse import parse_output
import celery
import requests

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument(
    '--local',
    action='store_true',
    help='An optional boolean argument'
)
args = arg_parser.parse_args()

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


def reget_onts_by_port(port: int, onts: list[dict], conn: ConnectHandler):
    _onts = conn.send_command(f'display ont info {port}', use_textfsm=True)
    _onts_sn = [ont["serial_number"] for ont in _onts]
    onts = [ont for ont in onts
            if ont["serial_number"] in _onts_sn]
    for ont in onts:
        for _ont in _onts:
            if ont["serial_number"] == _ont["serial_number"]:
                ont["ont_id"] = _ont["ont_id"]
    return onts


def add_optical_info_to_onts(port: int, onts: list[dict], conn: ConnectHandler):
    optical_output = conn.send_command(
        f"display ont optical-info {port} all",
        use_textfsm=True
    )
    if len(optical_output) != len(onts):
        onts = reget_onts_by_port(port, onts, conn)
    for ont in onts:
        voltage = next(
            (item for item in optical_output
             if item["ont_id"] == ont["ont_id"]),
            None)
        ont["voltage"] = voltage["voltage"]
    return onts


def add_gemport_to_onts(port: int, onts: list[dict], conn: ConnectHandler):
    for ont in onts:
        _onts = conn.send_command(f'display ont info {port}', use_textfsm=True)
        if len(_onts) != len(onts):
            onts = reget_onts_by_port(port, onts, conn)
        gem_output = conn.send_command(
            f"display ont gemport {port} ontid {ont['ont_id']}",
            use_textfsm=True,
        )
        ont["gem"] = gem_output
    return onts


def add_vlan_to_onts(port: int, onts: list[dict], conn: ConnectHandler):
    for ont in onts:
        ont["vlan"] = []
        for j in range(1, 5):
            _onts = conn.send_command(f'display ont info {port}', use_textfsm=True)
            if len(_onts) != len(onts):
                onts = reget_onts_by_port(port, onts, conn)
            if ont not in onts:
                break
            vlan_output = conn.send_command(
                f"display ont port vlan {port} {ont['ont_id']} byport eth {j}", # noqa
                use_textfsm=True
            )
            ont["vlan"].append(vlan_output)
    return onts


def add_snmp_to_onts(port: int, onts: list[dict], conn: ConnectHandler):
    for ont in onts:
        _onts = conn.send_command(f'display ont info {port}', use_textfsm=True)
        if len(_onts) != len(onts):
            onts = reget_onts_by_port(port, onts, conn)
        snmp_output = conn.send_command(
            f"display ont snmp-profile {port} all",
            use_textfsm=True
        )
        snmp_output = next(
            (snmp for snmp in snmp_output
                if snmp["ont_id"] == ont["ont_id"]),
            None
        )
        if snmp_output:
            ont["snmp"] = {
                'snmp_profile_id': snmp_output["snmp_profile_id"],
                'snmp_profile_name': snmp_output["snmp_profile_name"],
            }
        else:
            ont["snmp"] = {}
    return onts


def get_onts_by_port(port: int):
    onts = []
    with ConnectHandler(**credentials) as conn:
        conn.enable()
        print("Looking for onts in port", port)
        conn.send_command("config", auto_find_prompt=False)
        conn.find_prompt()
        conn.send_command("interface gpon 0/0", auto_find_prompt=False)
        conn.find_prompt()
        onts = conn.send_command(f"display ont info {port}", use_textfsm=True)
        onts = add_optical_info_to_onts(port, onts, conn)
        onts = add_gemport_to_onts(port, onts, conn)
        onts = add_vlan_to_onts(port, onts, conn)
        onts = add_snmp_to_onts(port, onts, conn)
        conn.send_command("quit", auto_find_prompt=False)
        conn.find_prompt()
        onts = [
            {
                "fsp": f"0/0/{port}",
                "ont": ont["ont_id"],
                "sn": ont["serial_number"],
                "gem": ont["gem"],
                "vlan": ont["vlan"],
                "snmp": ont["snmp"],
                "registered": True,
                "voltage": ont["voltage"]
            }
            for ont in onts
        ]
    return onts


def get_boards_and_services():
    boards = None
    services = None
    with ConnectHandler(**credentials) as net_connect:
        boards = net_connect.send_command("display board 0", use_textfsm=True)
        services = net_connect.send_command("display sysman service state", use_textfsm=True)  # noqa
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
    onts = get_onts(n_ports, autofind=True) if not args.local else get_onts(2)
    info["onts"] = onts
    print("Notifying all info")
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
            onts = get_onts(n_ports) if not args.local else get_onts(2)
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
            chassis, slot, port = fsp.replace(" ", "").split("/")
            parsed_output = conn.send_command(
                f"display ont info {chassis} {slot} {port}",
                use_textfsm=True
            )
            prev_id = next(
                (_ont["ont_id"] for _ont in parsed_output
                 if _ont["serial_number"] == sn),
                None
            )
            conn.send_command(
                f"interface gpon {chassis}/{slot}",
                auto_find_prompt=False
            )
            conn.find_prompt()
            conn.send_command(f"ont delete {port} {prev_id}")
            parsed_output = conn.send_command(
                "display ont autofind {port}",
                use_textfsm=True
            )
            autofind_ont = next(
                (_ont for _ont in parsed_output
                 if _ont["serial_number"].split()[0] == sn),
                None)
        else:
            chassis, slot, port = autofind_ont["fsp"].replace(" ", "").split("/")
            conn.send_command(
                f"interface gpon {chassis}/{slot}",
                auto_find_prompt=False
            )
            conn.find_prompt()
        parsed_output = conn.send_command(
            f"ont add {port} sn-auth {sn} omci ont-lineprofile-id 500 ont-srvprofile-id 500 desc {sn}", # noqa
            use_textfsm=True
        )
        if parsed_output[0]["success"] != '1':
            raise Exception("ONT not registered")
        register_lock.release()
        conn.send_command("quit", auto_find_prompt=False)
        conn.find_prompt()
    onts = get_onts_by_port(int(port))
    new_ont = next((ont for ont in onts if ont["sn"] == sn), None)
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
