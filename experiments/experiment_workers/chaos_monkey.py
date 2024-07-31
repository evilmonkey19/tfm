import requests
import random
import time
import logging
import argparse

# urls = {
#     f"site_{i}": f"http://localhost:800{i}"
#     for i in range(1, 11)
# }


args = argparse.ArgumentParser()

args.add_argument(
    "--sites",
    type=int,
    default=10,
    help="Number of sites to target"
)

args.add_argument(
    "--tried",
    type=int,
    default=1,
    help="Number of times the chaos monkey has been tried"
)

args.add_argument(
    "--only",
    type=str,
    help="only one action to perform",
)

args = args.parse_args()

SITES = args.sites
TRY = args.tried

urls = {
    f"site_{i}": f"http://localhost:800{i}/api"
    for i in range(1, SITES + 1)
}

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
        if args.only is None:
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

if __name__ == '__main__':
    logging.info("Starting chaos monkey")
    while True:
        try:
            time.sleep(random.uniform(0, 10))
            action = random.choice(actions, weights=weights)[0]
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
                    board = requests.get(urls[site] + "/hosts/OLT/change_board_state", timeout=20)
                    logging.info("%s: Changing board state to ", site)
                case "ont_change_voltage":
                    onts = requests.get(urls[site] + "/hosts/OLT/list_onts", timeout=20).json()["onts"]
                    ont = random.choice(onts)
                    current_state = float(ont["voltage_v"])
                    if 3.2 <= current_state <= 3.4:
                        changing_state = random.choice(["set_low_voltage", "set_high_voltage"])
                    else:
                        changing_state = "set_normal_voltage"
                    requests.get(urls[site] + f"/hosts/OLT/ont/{ont['sn']}/{changing_state}", timeout=20)
                    logging.info("Changing voltage for %s from %s to %s", ont['sn'], site, changing_state)
                case "change gemport":
                    onts = requests.get(urls[site] + "/hosts/OLT/list_onts", timeout=20).json()["onts"]
                    ont = random.choice(onts)
                    requests.get(urls[site] + f"/hosts/OLT/ont/{ont['sn']}/set_gemport_0/1", timeout=20)
                    logging.info("Changing gemport for %s from %s", ont['sn'], site)
                case "change_c_vlan":
                    onts = requests.get(urls[site] + "/hosts/OLT/list_onts", timeout=20).json()["onts"]
                    ont = random.choice(onts)
                    requests.get(urls[site] + f"/hosts/OLT/ont/{ont['sn']}/port_eth/{random.randint(1,4)}/set_c_vlan/99", timeout=20)
                    logging.info("Changing c vlan for %s from %s", ont['sn'], site)
                case "change_s_vlan":
                    onts = requests.get(urls[site] + "/hosts/OLT/list_onts", timeout=20).json()["onts"]
                    ont = random.choice(onts)
                    requests.get(urls[site] + f"/hosts/OLT/ont/{ont['sn']}/port_eth/{random.randint(1,4)}/set_s_vlan/99", timeout=20)
                    logging.info("Changing s vlan for %s from %s", ont['sn'], site)
                case "change_vlan_type":
                    onts = requests.get(urls[site] + "/hosts/OLT/list_onts", timeout=20).json()["onts"]
                    ont = random.choice(onts)
                    requests.get(urls[site] + f"/hosts/OLT/ont/{ont['sn']}/port_eth/{random.randint(1,4)}/change_vlan_type", timeout=20)
                    logging.info("Changing vlan type for %s from %s", ont['sn'], site)
                case "change_snmp_profile":
                    onts = requests.get(urls[site] + "/hosts/OLT/list_onts", timeout=20).json()["onts"]
                    ont = random.choice(onts)
                    requests.get(urls[site] + f"/hosts/OLT/ont/{ont['sn']}/snmp_profile/{random.randint(2,10)}", timeout=20)
                    logging.info("Changing snmp profile for %s from %s", ont['sn'], site)
                case "unregister ont":
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
                    service = random.choice(services.keys())
                    requests.get(urls[site] + f"/hosts/OLT/change_service_state/{service}", timeout=20)
                    logging.info("Changing state of %s from %s", service, site)
                case other:
                    logging.info("No action taken for %s", site)
        except requests.exceptions.Timeout:
            logging.info("Timeout error with %s", site)
        except requests.exceptions.ConnectionError:
            logging.info("Connection error with %s", site)
        except KeyboardInterrupt:
            break
    logging.info("Exiting chaos monkey")
