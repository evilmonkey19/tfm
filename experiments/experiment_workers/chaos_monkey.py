import requests
import random
import time
import logging
import argparse

# urls = {
#     f"site_{i}": f"http://localhost:800{i}"
#     for i in range(1, 11)
# }

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("chaos_monkey.log"),
        logging.StreamHandler()
    ]
)

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

args = args.parse_args()

FACTOR = args.factor
SITES = args.sites

urls = {
    f"site_{i}": f"http://localhost:800{i}/api"
    for i in range(1, SITES + 1)
}



if __name__ == '__main__':
    while True:
        try:
            time.sleep(random.uniform(0, 10))
            site = random.choice(list(urls.keys()))
            if random.random() < min(0.0000000001*FACTOR, 1):
                host = requests.get(urls[site] + "/hosts", timeout=20).json()["hosts"][0]["OLT"]
                if host["running"]:
                    requests.get(urls[site] + "/hosts/OLT/shutdown", timeout=20)
                    logging.info("Shutting down %s", host)
                else:
                    requests.get(urls[site] + "/hosts/OLT/start", timeout=20)
                    logging.info("Starting %s", host)
            elif random.random() < min(0.2*FACTOR, 1):
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
