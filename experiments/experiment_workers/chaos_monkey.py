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
    help="only one action to perform",
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


pattern = r"^chaos_monkey_(\d+)?_try_(\d+)?"
filenames = os.listdir()
highest_try = 0
highest_sites = 0

for filename in filenames:
    if match := re.match(pattern, filename):
        print(filename)
        sites = int(match.group(1))
        highest_sites = max(highest_sites, sites)
        last_try = int(match.group(2))
        highest_try = max(highest_try, last_try)

print("Highest sites:", highest_sites)
print("Highest try:", highest_try)

if highest_try == 10:
    highest_sites += 1
    highest_try = 0
TRY = highest_try + 1
SITES = max(highest_sites, 1)
print

urls = {
    f"site_{i}": f"http://localhost:800{i}/api"
    for i in range(1, SITES + 1)
}

urls_ready = {
    f'site_{i}': False for i in range(1, SITES + 1)
}


actions = []
weights = []
logging_file = f"chaos_monkey_{SITES}_try_{TRY}.log"
match args.only:
    case "misconfigurations":
        actions = [action[0] for action in misconfigurations]
        weights = [action[1] for action in misconfigurations]
        logging_file = f"chaos_monkey_{SITES}_try_{TRY}_only_misconfigurations.log"
    case "errors":
        actions = [action[0] for action in errors]
        weights = [action[1] for action in errors]
        logging_file = f"chaos_monkey_{SITES}_try_{TRY}_only_errors.log"
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
            logging_file = f"chaos_monkey_{SITES}_try_{TRY}_only_{args.only}.log"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[
        logging.FileHandler(logging_file),
        logging.StreamHandler()
    ],
)
logging.Formatter(
    datefmt="%Y-%m-%d %H:%M:%S",
    fmt='%(asctime)s.%(msecs)03d',
)

logging.info(f"Chaos monkey started with {SITES} sites. Try {TRY} and options {args.only}.")

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
                started = True
            time.sleep(random.uniform(0, 10))
            action = random.choices(actions, weights=weights)[0]
            site = random.choice(list(urls.keys()))
            match action:
                case "reboot":
                    host = requests.get(urls[site] + "/hosts", timeout=20).json()["hosts"][0]["OLT"]
                    if host["running"]:
                        requests.get(urls[site] + "/hosts/OLT/shutdown", timeout=20)
                        logging.info("%s: Shutting down %s", site, host)
                        time.sleep(random.uniform(0, 10))
                        requests.get(urls[site] + "/hosts/OLT/start", timeout=20)
                        logging.info("%s: Starting %s", site, host)
                case "change_board_state":
                    status = requests.get(urls[site] + "/hosts/OLT/change_board_state", timeout=20).json()["status"]
                    logging.info("%s: Changing board state to %s", site, status)
                case "ont_change_voltage":
                    onts = requests.get(urls[site] + "/hosts/OLT/list_onts", timeout=20).json()["onts"]
                    onts = [ont for ont in onts if ont["registered"]]
                    ont = random.choice(onts)
                    current_state = float(ont["voltage_v"])
                    if 3.2 <= current_state <= 3.4:
                        changing_state = random.choice(["set_low_voltage", "set_high_voltage"])
                    else:
                        changing_state = "set_normal_voltage"
                    requests.get(urls[site] + f"/hosts/OLT/ont/{ont['sn']}/{changing_state}", timeout=20)
                    logging.info("Changing voltage for %s from %s to %s", ont['sn'], site, changing_state)
                case "change_gemport":
                    onts = requests.get(urls[site] + "/hosts/OLT/list_onts", timeout=20).json()["onts"]
                    onts = [ont for ont in onts if ont["registered"]]
                    ont = random.choice(onts)
                    requests.get(urls[site] + f"/hosts/OLT/ont/{ont['sn']}/set_gemport_0/1", timeout=20)
                    logging.info("Changing gemport for %s from %s", ont['sn'], site)
                case "change_c_vlan":
                    onts = requests.get(urls[site] + "/hosts/OLT/list_onts", timeout=20).json()["onts"]
                    onts = [ont for ont in onts if ont["registered"]]
                    ont = random.choice(onts)
                    requests.get(urls[site] + f"/hosts/OLT/ont/{ont['sn']}/port_eth/{random.randint(1,4)}/c__vlan/99", timeout=20)
                    logging.info("Changing c vlan for %s from %s", ont['sn'], site)
                case "change_s_vlan":
                    onts = requests.get(urls[site] + "/hosts/OLT/list_onts", timeout=20).json()["onts"]
                    onts = [ont for ont in onts if ont["registered"]]
                    ont = random.choice(onts)
                    requests.get(urls[site] + f"/hosts/OLT/ont/{ont['sn']}/port_eth/{random.randint(1,4)}/s__vlan/99", timeout=20)
                    logging.info("Changing s vlan for %s from %s", ont['sn'], site)
                case "change_vlan_type":
                    onts = requests.get(urls[site] + "/hosts/OLT/list_onts", timeout=20).json()["onts"]
                    onts = [ont for ont in onts if ont["registered"]]
                    ont = random.choice(onts)
                    requests.get(urls[site] + f"/hosts/OLT/ont/{ont['sn']}/port_eth/{random.randint(1,4)}/change_vlan__type", timeout=20)
                    logging.info("Changing vlan type for %s from %s", ont['sn'], site)
                case "change_snmp_profile":
                    onts = requests.get(urls[site] + "/hosts/OLT/list_onts", timeout=20).json()["onts"]
                    onts = [ont for ont in onts if ont["registered"]]
                    ont = random.choice(onts)
                    requests.get(urls[site] + f"/hosts/OLT/ont/{ont['sn']}/snmp_profile/{random.randint(2,10)}", timeout=20)
                    logging.info("Changing snmp profile for %s from %s", ont['sn'], site)
                case "unregister_ont":
                    onts = requests.get(urls[site] + "/hosts/OLT/list_onts", timeout=20).json()["onts"]
                    registered_onts = [ont for ont in onts if ont["registered"]]
                    ont = random.choice(registered_onts)
                    logging.info("Unregistering %s from %s", ont['sn'], site)
                    requests.get(urls[site] + f"/hosts/OLT/unregister_ont/{ont['sn']}", timeout=20)
                    onts = requests.get(urls[site] + "/hosts/OLT/list_onts", timeout=20).json()["onts"]
                    if ont['sn'] not in [ont['sn'] for ont in onts if ont['registered']]:
                        logging.info("%s successfully unregistered from %s", ont['sn'], site)
                    else:
                        logging.info("Failed to unregister %s from %s", ont['sn'], site)
                case "change_service_state":
                    services = requests.get(urls[site] + "/hosts/OLT/services", timeout=20).json()["services"]
                    service = random.choice(list(services.keys()))
                    requests.get(urls[site] + f"/hosts/OLT/change_service_state/{service}", timeout=20)
                    logging.info("Changing state of %s from %s", service, site)
                case other:
                    logging.info("No action taken for %s", site)
        except requests.exceptions.Timeout:
            logging.info("Timeout error with %s", site)
        except requests.exceptions.ConnectionError:
            logging.info("Connection error with %s", site)
        except KeyboardInterrupt:
            logging.info("Exiting chaos monkey KeyboardInterrupt")
            break
    logging.info("Exiting chaos monkey")


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
    uvicorn.run(app, port=3500)