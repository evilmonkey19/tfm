from datetime import datetime
import os
import re
import random
import threading
import time
import logging
import argparse
from fastapi.concurrency import asynccontextmanager
import requests

import fastapi
import uvicorn

everything_ready = threading.Event()
everything_ready.clear()

stop_thread = threading.Event()
stop_thread.clear()

args = argparse.ArgumentParser()

args.add_argument(
    "--only",
    type=str,
    help="only one action to perform [misconfigurations, errors, all, nothing]"
)
args.add_argument(
    "--local",
    action="store_true",
    help="run chaos monkey locally"
)
args = args.parse_args()

misconfigurations = [
    ("change_gemport", 0.2),
    ("change_c_vlan", 0.2),
    ("change_s_vlan", 0.2),
    ("change_vlan_type", 0.2),
    ("change_snmp_profile", 0.2),
    ("unregister_ont", 0.2),
    ("change_service_state", 0.2)
]
errors = [
    ("reboot", 0.01),
    ("change_board_state", 0.1),
    ("ont_change_voltage", 0.1),
]


pattern = r"^chaos_monkey_(\d+)?_try_(\d+)?_only_misconfigurations.*\.csv$"
filenames = os.listdir()
max_sites_try = (0, 0)

for filename in filenames:
    if match := re.match(pattern, filename):
        sites_try = (int(match.group(1)), int(match.group(2)))
        if sites_try[0] > max_sites_try[0] or \
            (sites_try[0] == max_sites_try[0] and sites_try[1] > max_sites_try[1]):
            max_sites_try = sites_try

if max_sites_try[1] == 10:
    max_sites_try = (max_sites_try[0] + 1, 0)
max_sites_try = (max_sites_try[0], max_sites_try[1] + 1)
SITES = max_sites_try[0] if max_sites_try[0] > 0 else 1
TRY = max_sites_try[1]

urls = {
    f"site_{i}": f"http://192.168.{i}.3:8000/api" if not args.local else f"http://localhost:8000/api"
    for i in range(1, SITES + 1)
}

urls_ready = {
    f'site_{i}': False for i in range(1, SITES + 1)
}

events = []
actions = []
weights = []
logging_file = f"chaos_monkey_{SITES}_try_{TRY}.csv"
match args.only:
    case "misconfigurations":
        actions = [action[0] for action in misconfigurations]
        weights = [action[1] for action in misconfigurations]
        logging_file = f"chaos_monkey_{SITES}_try_{TRY}_only_misconfigurations.csv"
    case "errors":
        actions = [action[0] for action in errors]
        weights = [action[1] for action in errors]
        logging_file = f"chaos_monkey_{SITES}_try_{TRY}_only_errors.csv"
    case other:
        if args.only is None or args.only == "all":
            actions = [action[0] for action in misconfigurations + errors]
            weights = [action[1] for action in misconfigurations + errors]
        else:
            if args.only in [action[0] for action in misconfigurations + errors]:
                actions = [args.only]
                weights = [1]
            else:
                actions = ["no_action"]
                weights = [1]
            logging_file = f"chaos_monkey_{SITES}_try_{TRY}_only_{args.only}.csv"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ],
)
logging.Formatter(
    datefmt="%Y-%m-%d %H:%M:%S",
    fmt='%(asctime)s.%(msecs)03d',
)

logging.info(f"Chaos monkey started with {SITES} sites. Try {TRY} and options {args.only}.")


def register_event(site, event):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S_%f")[:-3]
    return (f"{site},{event},{timestamp}")


recent_onts = {
    site: [] for site in urls.keys()
}


def pick_random_ont(site):
    for site, onts in recent_onts.items():
        recent_onts[site] = [ont for ont in onts if time.time() - list(ont.values())[0] < 600]
    onts = requests.get(urls[site] + "/hosts/OLT/list_onts", timeout=20).json()["onts"]
    onts = [ont for ont in onts if ont["registered"]]
    onts = [ont for ont in onts if ont not in recent_onts[site]]
    if args.local:
        onts = [ont for ont in onts if ont["fsp"] in ["0/0/0", "0/0/1"]]
    ont = random.choice(onts)
    recent_onts[site].append({ont["sn"]: time.time()})
    return ont


def on_exit():
    logging.info("Exiting chaos monkey")
    events.append(register_event("_", "Exiting chaos monkey"))
    with open(logging_file, "w") as f:
        for event in events:
            f.write(event + "\n")


def chaos_monkey():
    started = False
    while True:
        if stop_thread.is_set():
            break
        try:
            if not everything_ready.is_set():
                time.sleep(2)
                logging.info("Waiting for all sites to be ready")
                continue
            if not started:
                logging.info("Starting chaos monkey")
                events.append(register_event("_", "Starting chaos monkey"))
                started = True
            time.sleep(random.uniform(0, 20//SITES))
            action = random.choices(actions, weights=weights)[0]
            site = random.choice(list(urls.keys()))
            if random.random() < 0.7:
                continue
            match action:
                case "reboot":
                    host = requests.get(urls[site] + "/hosts", timeout=20).json()["hosts"][0]["OLT"]
                    if host["running"]:
                        requests.get(urls[site] + "/hosts/OLT/shutdown", timeout=20)
                        logging.info("%s: Shutting down %s", site, host)
                        events.append(register_event(site, f"Shutting down {host}"))
                        time.sleep(random.uniform(0, 10))
                        requests.get(urls[site] + "/hosts/OLT/start", timeout=20)
                        logging.info("%s: Starting %s", site, host)
                        events.append(register_event(site, f"Starting {host}"))
                case "change_board_state":
                    status = requests.get(urls[site] + "/hosts/OLT/change_board_state", timeout=20).json()["status"]
                    logging.info("%s: Changing board state to %s", site, status)
                    events.append(register_event(site, f"Changing board state to {status}"))
                case "ont_change_voltage":
                    ont = pick_random_ont(site)
                    current_state = float(ont["voltage_v"])
                    if 3.2 <= current_state <= 3.4:
                        changing_state = random.choice(["set_low_voltage", "set_high_voltage"])
                    else:
                        changing_state = "set_normal_voltage"
                    requests.get(urls[site] + f"/hosts/OLT/ont/{ont['sn']}/{changing_state}", timeout=20)
                    logging.info("Changing voltage for %s from %s to %s", ont['sn'], site, changing_state)
                    events.append(register_event(site, f"Changing voltage for {ont['sn']} from {site} to {changing_state}"))
                case "change_gemport":
                    ont = pick_random_ont(site)
                    requests.get(urls[site] + f"/hosts/OLT/ont/{ont['sn']}/set_gemport_0/1", timeout=20)
                    logging.info("Changing gemport for %s from %s", ont['sn'], site)
                    events.append(register_event(site, f"Changing gemport for {ont['sn']} from {site}"))
                case "change_c_vlan":
                    ont = pick_random_ont(site)
                    requests.get(urls[site] + f"/hosts/OLT/ont/{ont['sn']}/port_eth/{random.randint(1,4)}/c__vlan/99", timeout=20)
                    logging.info("Changing c vlan for %s from %s", ont['sn'], site)
                    events.append(register_event(site, f"Changing c vlan for {ont['sn']} from {site}"))
                case "change_s_vlan":
                    ont = pick_random_ont(site)
                    requests.get(urls[site] + f"/hosts/OLT/ont/{ont['sn']}/port_eth/{random.randint(1,4)}/s__vlan/99", timeout=20)
                    logging.info("Changing s vlan for %s from %s", ont['sn'], site)
                    events.append(register_event(site, f"Changing s vlan for {ont['sn']} from {site}"))
                case "change_vlan_type":
                    ont = pick_random_ont(site)
                    requests.get(urls[site] + f"/hosts/OLT/ont/{ont['sn']}/port_eth/{random.randint(1,4)}/change_vlan__type", timeout=20)
                    logging.info("Changing vlan type for %s from %s", ont['sn'], site)
                    events.append(register_event(site, f"Changing vlan type for {ont['sn']} from {site}"))
                case "change_snmp_profile":
                    ont = pick_random_ont(site)
                    requests.get(urls[site] + f"/hosts/OLT/ont/{ont['sn']}/snmp_profile/{random.randint(2,10)}", timeout=20)
                    logging.info("Changing snmp profile for %s from %s", ont['sn'], site)
                    events.append(register_event(site, f"Changing snmp profile for {ont['sn']} from {site}"))
                case "unregister_ont":
                    ont = pick_random_ont(site)
                    logging.info("Unregistering %s from %s", ont['sn'], site)
                    requests.get(urls[site] + f"/hosts/OLT/unregister_ont/{ont['sn']}", timeout=20)
                    onts = requests.get(urls[site] + "/hosts/OLT/list_onts", timeout=20).json()["onts"]
                    if ont['sn'] not in [ont['sn'] for ont in onts if ont['registered']]:
                        logging.info("%s successfully unregistered from %s", ont['sn'], site)
                        events.append(register_event(site, f"Unregistering {ont['sn']} from {site}"))
                    else:
                        logging.info("Failed to unregister %s from %s", ont['sn'], site)
                        events.append(register_event(site, f"Failed to unregister {ont['sn']} from {site}"))
                case "change_service_state":
                    services = requests.get(urls[site] + "/hosts/OLT/services", timeout=20).json()["services"]
                    service = random.choice(list(services.keys()))
                    requests.get(urls[site] + f"/hosts/OLT/change_service_state/{service}", timeout=20)
                    logging.info("Changing state of %s from %s", service, site)
                    events.append(register_event(site, f"Changing state of {service} from {site}"))
                case other:
                    logging.info("No action taken for %s", site)
                    events.append(register_event(site, "No action taken"))
        except requests.exceptions.Timeout:
            logging.info("Timeout error with %s", site)
            events.append(register_event(site, "Timeout error"))
        except requests.exceptions.ConnectionError:
            logging.info("Connection error with %s", site)
            events.append(register_event(site, "Connection error"))
        except KeyboardInterrupt:
            logging.info("Exiting chaos monkey KeyboardInterrupt")
            events.append(register_event(site, "Exiting chaos monkey KeyboardInterrupt"))
            break
    on_exit()


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    stop_thread.clear()
    chaos_monkey_task = threading.Thread(target=chaos_monkey)
    chaos_monkey_task.start()
    yield
    stop_thread.set()
    chaos_monkey_task.join()


app = fastapi.FastAPI(lifespan=lifespan)

@app.post("/{site}/ready")
async def set_ready(site: str):
    urls_ready[site] = True
    print(urls_ready)
    if all(urls_ready.values()):
        everything_ready.set()
    return {"status": "ready"}

if __name__ == '__main__':
    uvicorn.run(app, port=3500, host="0.0.0.0")
