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
    "--factor",
    type=int,
    default=1,
    help="Factor to increase the number of sites"
)

args.add_argument(
    "--tried",
    type=int,
    default=1,
    help="Number of times the chaos monkey has been tried"
)

args.add_argument(
    "--only-shutting-down",
    action="store_true",
    help="Only shut down the hosts"
)

args = args.parse_args()

factor_val = args.factor
SITES = args.sites
TRY = args.tried
ONLY_SHUTTING_DOWN = args.only_shutting_down

urls = {
    f"site_{i}": f"http://localhost:800{i}/api"
    for i in range(1, SITES + 1)
}

logging_file = f"chaos_monkey_{SITES}_try_{TRY}.log"
if ONLY_SHUTTING_DOWN:
    factor_val = 60
    logging_file = f"chaos_monkey_{SITES}_try_{TRY}_only_shutting_down.log"
FACTOR = factor_val
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

logging.info(f"Chaos monkey started with {SITES} sites and factor {FACTOR}. Try {TRY}. Only shutting down: {ONLY_SHUTTING_DOWN}")

if __name__ == '__main__':
    logging.info("Starting chaos monkey")
    while True:
        try:
            time.sleep(random.uniform(0, 10))
            site = random.choice(list(urls.keys()))
            if random.random() < min(0.01*FACTOR, 1):
                host = requests.get(urls[site] + "/hosts", timeout=20).json()["hosts"][0]["OLT"]
                if host["running"]:
                    requests.get(urls[site] + "/hosts/OLT/shutdown", timeout=20)
                    logging.info("%s: Shutting down %s", site, host)
                    time.sleep(random.uniform(0, 10))
                    requests.get(urls[site] + "/hosts/OLT/start", timeout=20)
                    logging.info("%s: Starting %s", site, host)
            elif random.random() < min(0.2*FACTOR, 1) and not ONLY_SHUTTING_DOWN:
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
            else:
                logging.info("No action taken for %s", site)
        except requests.exceptions.ConnectionError:
            logging.info("Connection error with %s", site)
        except KeyboardInterrupt:
            break
    logging.info("Exiting chaos monkey")
