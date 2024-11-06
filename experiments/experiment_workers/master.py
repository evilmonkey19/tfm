from dataclasses import dataclass, field
import os
import time
from datetime import datetime
from threading import Lock, Event
import subprocess
import threading
import uuid
import copy
import argparse

import celery
import yaml

from worker import register_ont, fix_service

args = argparse.ArgumentParser()
args.add_argument(
    "--local",
    action="store_true",
    help="Run the script locally"
)
args = args.parse_args()

RABBITMQ_IP = os.environ.get('RABBITMQ_IP', 'localhost')

print(f'Connecting to RabbitMQ at {RABBITMQ_IP}')

REDIS_IP = os.environ.get('REDIS_IP', 'localhost')

app = celery.Celery(
    'master',
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
    worker_pool='solo',
)


@dataclass
class FixObject:
    site: str
    is_ont: bool
    error_type: str
    ont_or_service: dict
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    result = None


general_lock = Lock()
recently_fixed_lock = Lock()
original_all_info = dict()
all_info = dict()
events = list()
to_fix = list()
recently_fixed = dict()
olt_down = Event()
end_thread = Event()
start_running = Event()
round_finished = Event()


def register_event(site=None, event=None, fix=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S_%f")[:-3]
    if site is not None and event is not None:
        events.append(f"{timestamp},,{site},error,{event}")
        return
    if fix.result is None:
        if fix.is_ont:
            events.append(
                f"{timestamp},{fix.uuid},{fix.site},detected,{fix.error_type},{fix.ont_or_service['sn']}"
            )
        else:
            events.append(
                f"{timestamp},{fix.uuid},{fix.site},detected,{fix.error_type},{fix.ont_or_service['network_service']}"
            )
        return
    if fix.is_ont:
        events.append(
            f"{timestamp},{fix.uuid},{fix.site},fixed,{fix.error_type},{fix.ont_or_service['sn']}"
        )
    else:
        events.append(
            f"{timestamp},{fix.uuid},{fix.site},fixed,{fix.error_type},{fix.ont_or_service['network_service']}"
        )

def add_to_fix(site, ont_or_service, error_type):
    is_ont = "ont" in ont_or_service
    fix = FixObject(
        site=site,
        is_ont=is_ont,
        error_type=error_type,
        ont_or_service=ont_or_service
    )
    with general_lock:
        if any(
            fix.site == f.site
            and fix.ont_or_service == f.ont_or_service
            for f in to_fix
        ):
            return
        to_fix.append(fix)
        register_event(fix=fix)


def fixer():
    while not end_thread.is_set():
        time.sleep(1)
        try:
            if olt_down.is_set():
                continue
            with general_lock:
                print(f"Fix queue: {len(to_fix)}")
                for fix in to_fix:
                    if fix.result is not None:
                        if fix.result.ready():
                            print(
                                "Fixing "
                                + fix.error_type
                                + " in site "
                                + fix.site +
                                " finished"
                            )
                            if fix.is_ont:
                                result = fix.result.get(
                                    disable_sync_subtasks=False
                                )
                                all_info[fix.site]["onts"].append(result)
                                with recently_fixed_lock:
                                    recently_fixed[fix.site].append(result["sn"])
                            register_event(fix=fix)
                            to_fix.remove(fix)
                    elif fix.is_ont:
                        fix.result = register_ont.apply_async(
                            args=(
                                fix.ont_or_service["fsp"],
                                fix.ont_or_service["sn"],
                            ), queue=fix.site
                        )
                    elif not fix.is_ont:
                        fix.result = fix_service.apply_async(
                            args=(fix.ont_or_service,),
                            queue=fix.site
                        )
                        print(f"Fixing service {fix.ont_or_service['network_service']} in site {fix.site}: {fix.uuid}") # noqa
        except (Exception,) as e:
            if olt_down.is_set():
                to_fix.clear()
            else:
                print(e)


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
    correct_onts = [
        ont for ont in info["onts"]
        if ont['sn'] in [ont['sn'] for ont in real_onts]
    ]
    row = {
        "site_name": site_name,
        "real_onts": len(real_onts),
        "detected_onts": len(info["onts"]),
        "correct_onts": len(correct_onts),
    }
    with open('results_detected_onts.csv', 'a') as f:
        f.write(f"{row['site_name']},"
                f"{row['real_onts']},"
                f"{row['detected_onts']},"
                f"{row['correct_onts']}\n")
    info["onts"] = [ont for ont in info["onts"] if ont["registered"]]
    with general_lock:
        all_info[site_name] = info
        original_all_info[site_name] = info
        recently_fixed[site_name] = []
    print("All info received!")
    start_running.set()
    # with open('testing.json', 'w') as f:
    #     import json
    #     json.dump(info, f)

############################################
#                                          #
#               TASKS                      #
#                                          #
############################################


@app.task
def notify_olt(queue, status: str):
    register_event(site=queue, event=f"OLT is {status}")
    if status == "down":
        olt_down.set()
        print("OLT is down")
    else:
        olt_down.clear()
        with general_lock:
            all_info[queue] = original_all_info[queue]
        print("OLT is up")


@app.task
def notify_boards_and_services(queue, boards: list, services: list):
    if not boards == all_info[queue]["boards"]:
        register_event(
            site=queue,
            event=f"Boards: board 4 is {boards[4]['status']}"
        )
        all_info[queue]["boards"] = boards
        print("Board 4 is down")

    if not services == original_all_info[queue]["services"]:
        changed_service = [
            s for s in services for s2 in all_info[queue]["services"]
            if s["network_service"] == s2["network_service"]
            and s["state"] != s2["state"]]
        if changed_service:
            for service in changed_service:
                add_to_fix(queue, service, "service changed")


def move_onts(queue, sn: str):
    onts: list = all_info[queue]["onts"]
    ont = next((ont for ont in onts if ont["sn"] == sn), None)
    if ont is None:
        return
    all_info[queue]["onts"].remove(ont)

    _onts = [ont for ont in onts if ont["fsp"] == ont["fsp"]]
    for _ont in _onts:
        if int(_ont["ont"]) > int(ont["ont"]):
            _ont["ont"] = str(int(_ont["ont"]) - 1)


@app.task
def notify_onts(queue, onts: list):
    with recently_fixed_lock:
        print("Checking unregistered ONTs")
        check_unregistered_onts(queue, onts)
        print("Checking GemPort misconfigurations")
        check_gemport_misconfigurations(queue, onts)
        print("Checking C__VLAN misconfigurations")
        check_c__vlan_misconfigurations(queue, onts)
        print("Checking S__VLAN misconfigurations")
        check_s__vlan_misconfigurations(queue, onts)
        print("Checking VLAN type misconfigurations")
        check_vlan_type_misconfigurations(queue, onts)
        print("Checking SNMP profile misconfigurations")
        check_snmp_profile_misconfigurations(queue, onts)
        check_onts_voltage(queue, onts)
        recently_fixed[queue] = []
        round_finished.set()


def check_unregistered_onts(queue, onts: list):
    onts_to_look = copy.deepcopy(all_info[queue]["onts"])
    onts_to_look = [ont for ont in onts_to_look
                    if ont["sn"] not in recently_fixed[queue]]
    onts = [ont for ont in onts if ont["sn"] not in recently_fixed[queue]]
    for ont_to_look in onts_to_look:
        if ont_to_look["sn"] not in [ont["sn"] for ont in onts]:
            move_onts(queue, ont_to_look["sn"])
            print(f"Unregistered ONT found: {ont_to_look['sn']}")
            add_to_fix(queue, ont_to_look, "unregistered")


def check_gemport_misconfigurations(queue, onts: list):
    all_info_onts = copy.deepcopy(all_info[queue]["onts"])
    onts_to_look = [ont for ont in all_info_onts
                    if ont["sn"] not in recently_fixed[queue]]
    incorrect_gemport_onts = []
    for ont_to_look in onts_to_look:
        try:
            ont = next(
                (_ont for _ont in onts
                    if _ont["sn"] == ont_to_look["sn"]),
                    None)
            if ont["gem"] != ont_to_look["gem"]:
                incorrect_gemport_onts.append(ont_to_look)
        except (Exception,):
            incorrect_gemport_onts.append(ont_to_look)
    for ont in incorrect_gemport_onts:
        move_onts(queue, ont["sn"])
        print("GEMPORT MISCONFIGURATION", ont["sn"])
        add_to_fix(queue, ont, "gemport")


def check_c__vlan_misconfigurations(queue, onts: list):
    all_info_onts = copy.deepcopy(all_info[queue]["onts"])
    onts_to_look = [ont for ont in all_info_onts
                    if ont["sn"] not in recently_fixed[queue]]
    incorrect_c__vlan_onts = []
    for ont_to_look in onts_to_look:
        try:
            ont = next(
                (_ont for _ont in onts
                    if _ont["sn"] == ont_to_look["sn"]),
                    None)
            if any(
                ont["vlan"][port][0]['c_vlan'] != ont_to_look["vlan"][port][0]['c_vlan']
                for port in range(4)
            ):
                incorrect_c__vlan_onts.append(ont_to_look)
        except (Exception,):
            incorrect_c__vlan_onts.append(ont_to_look)
    for ont in incorrect_c__vlan_onts:
        move_onts(queue, ont["sn"])
        print("C__VLAN MISCONFIGURATION", ont["sn"])
        add_to_fix(queue, ont, "c_vlan")


def check_s__vlan_misconfigurations(queue, onts: list):
    all_info_onts = copy.deepcopy(all_info[queue]["onts"])
    onts_to_look = [ont for ont in all_info_onts
                    if ont["sn"] not in recently_fixed[queue]]
    incorrect_s__vlan_onts = []
    for ont_to_look in onts_to_look:
        try:
            ont = next(
                (_ont for _ont in onts
                    if _ont["sn"] == ont_to_look["sn"]),
                    None)
            if any(
                    ont["vlan"][port][0]['s_vlan'] != ont_to_look["vlan"][port][0]['s_vlan']
                    for port in range(4)
                ):
                incorrect_s__vlan_onts.append(ont_to_look)
                break
        except (Exception,):
            incorrect_s__vlan_onts.append(ont_to_look)
    for ont in incorrect_s__vlan_onts:
        move_onts(queue, ont["sn"])
        print("S__VLAN MISCONFIGURATION", ont["sn"])
        add_to_fix(queue, ont, "s_vlan")


def check_vlan_type_misconfigurations(queue, onts: list):
    all_info_onts = copy.deepcopy(all_info[queue]["onts"])
    onts_to_look = [ont for ont in all_info_onts
                    if ont["sn"] not in recently_fixed[queue]]
    incorrect_vlan_type_onts = []
    for ont_to_look in onts_to_look:
        try:
            ont = next(
                (_ont for _ont in onts
                    if _ont["sn"] == ont_to_look["sn"]),
                None)
            if any(
                    ont["vlan"][port][0]['vlan_type'] != ont_to_look["vlan"][port][0]['vlan_type']
                    for port in range(4)
                ):
                incorrect_vlan_type_onts.append(ont_to_look)
                break
        except (Exception,):
            incorrect_vlan_type_onts.append(ont_to_look)
    for ont in incorrect_vlan_type_onts:
        move_onts(queue, ont["sn"])
        print("VLAN TYPE MISCONFIGURATION", ont["sn"])
        add_to_fix(queue, ont, "vlan_type")


def check_snmp_profile_misconfigurations(queue, onts: list):
    all_info_onts = copy.deepcopy(all_info[queue]["onts"])
    onts_to_look = [ont for ont in all_info_onts
                    if ont["sn"] not in recently_fixed[queue]]
    incorrect_snmp_profile_onts = []
    for ont_to_look in onts_to_look:
        try:
            ont = next(
                (_ont for _ont in onts
                    if _ont["sn"] == ont_to_look["sn"]),
                None)
            if ont["snmp"] != ont_to_look["snmp"]:
                incorrect_snmp_profile_onts.append(ont_to_look)
        except (Exception,):
            incorrect_snmp_profile_onts.append(ont_to_look)
    for ont in incorrect_snmp_profile_onts:
        move_onts(queue, ont["sn"])
        print("SNMP PROFILE MISCONFIGURATION", ont["sn"])
        add_to_fix(queue, ont, "snmp_profile")


def check_onts_voltage(queue, onts: list):
    onts = [ont for ont in onts if ont["sn"] not in recently_fixed[queue]]
    for ont in onts:
        all_info_ont = next(
            (_ont for _ont in all_info[queue]["onts"]
             if _ont["sn"] == ont["sn"]),
            None)
        if all_info_ont is None:
            continue
        if ont["voltage"] == all_info_ont["voltage"]:
            continue
        # Low voltage
        if float(ont["voltage"]) <= 3.0:
            # print("Value is too low for ", ont["sn"])
            register_event(
                site=queue,
                event=f"ONT {ont['sn']} has low voltage"
            )
        # High voltage
        elif float(ont["voltage"]) >= 3.6:
            # print("Value is too high for ", ont["sn"])
            register_event(
                site=queue,
                event=f"ONT {ont['sn']} has high voltage"
            )
        else:
            # print("Value is normal for ", ont["sn"])
            register_event(
                site=queue,
                event=f"ONT {ont['sn']} has normal voltage"
            )
        all_info_ont["voltage"] = ont["voltage"]


def timer(task, worker):
    rounds = 0
    while not start_running.is_set():
        time.sleep(1)
    while rounds < 5*len(all_info):
        while not round_finished.is_set():
            time.sleep(1)
        round_finished.clear()
        rounds += 1
    time.sleep(60)
    worker.stop()
    task.join()


if __name__ == '__main__':
    worker = None
    if not args.local:
        subprocess.run(["docker", "compose", "up", "-d", "--build"])
    task = threading.Thread(target=fixer, name='fixer', daemon=True)
    task.start()
    worker = app.Worker(
        include=['master'],
        loglevel='INFO',
        hostname=os.getenv('HOSTNAME', 'localhost'),
        queues=['celery', 'master'],
    )
    if not args.local:
        timer_thread = threading.Thread(
            target=timer,
            args=(task, worker),
            daemon=True
        )
        timer_thread.start()
    worker.start()
    with open('events_log.csv', 'a') as f:
        for event in events:
            f.write(f"{event}\n")
    if not args.local:
        subprocess.run(["docker", "compose", "stop"])
        time.sleep(2)
        subprocess.run(["docker", "compose", "down"])
