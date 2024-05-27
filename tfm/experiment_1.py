"""
This is the script for the first experiment.
The intention of such script is to
test how long does it take to retrieve 
and store the information of all the ONTs
into nautobot.
"""
from concurrent.futures import ThreadPoolExecutor
from pprint import pprint
import argparse
import random
import string
import time

from wonderwords import RandomSentence
from netmiko import ConnectHandler
from ntc_templates.parse import parse_output
from fakenos import FakeNOS
# import pynautobot
import yaml

parser = argparse.ArgumentParser()
parser.add_argument("--num_hosts", type=int, help="Number of hosts")
args = parser.parse_args()

num_hosts = args.num_hosts

s = RandomSentence()

def get_random_sn():
    """Returns a random serial number."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))


credentials = [{
    "host": "localhost",
    "username": "user",
    "password": "user",
    "device_type": "huawei_smartax",
    "port": i,
} for i in range(6000, 6000 + num_hosts)]

inventory = {
    "hosts": {
        f"R{i}": {
            "username": "user",
            "password": "user",
            "port": 6000 + i,
            "nos": {
                "plugin": "huawei_smartax.py",
            },
            "configuration_file": f"configs/config_{i}.yaml",
        } for i in range(num_hosts)
    }
}


configs = [{
    "frames": [{
        "frame_id": 0,
        "slots": [
            {
                "slotid": 0,
                "boardname": "A123ABCD",
                "status": "Normal",
                "subtype0": "",
                "subtype1": "",
                "online_offline": "",
            },
            {
                "slotid": 1,
                "boardname": "",
                "status": "",
                "subtype0": "",
                "subtype1": "",
                "online_offline": "",
            },
            {
                "slotid": 2,
                "boardname": "H901GPSFE",
                "status": "Normal",
                "subtype0": "",
                "subtype1": "",
                "online_offline": "",
                "ports": [[
                        {
                            "ont_id": i,
                            "sn": get_random_sn(),
                            "control_flag": random.choices(["active", "configuring"])[0],
                            "run_state": random.choices(["online", "offline"])[0],
                            "config_state": random.choices(["online", "normal", "failing"])[0],
                            "match_state": random.choices(["initial", "match", "mismatch"])[0],
                            "online_offline": random.choices(["online", "offline"])[0],
                            "protect_side": random.choices(["yes", "no"])[0],
                            "description": s.bare_bone_with_adjective()

                        } for i in range(32)] for j in range(16)]
            },
            {
                "slotid": 3,
                "boardname": "A123ABCD",
                "status": "Active_normal",
                "subtype0": "CPCF",
                "subtype1": "",
                "online_offline": "",
            },
            {
                "slotid": 4,
                "boardname": "A123ABCD",
                "status": "Standby_failed",
                "subtype0": "CPCF",
                "subtype1": "",
                "online_offline": "Offline",
            },
            {
                "slotid": 5,
                "boardname": "",
                "status": "",
                "subtype0": "",
                "subtype1": "",
                "online_offline": "",
            },
        ]
    }],
} for _ in range(num_hosts)]

for index, config in enumerate(configs):
    with open(f"configs/config_{index}.yaml", "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True)


def get_onts(credential):
    """Get ONT information from the OLT."""
    with ConnectHandler(**credential) as conn:
        for i in range(16):
            command = f"display ont info 0/2/{i}"
            output = conn.send_command(command)
            parsed = parse_output(platform="huawei_smartax", command=command, data=output)
        

with FakeNOS(inventory=inventory) as net:
    start_time = time.time()
    with ThreadPoolExecutor() as executor:
        executor.map(get_onts, credentials)
    finish_time = time.time()

print("#"*20)
print(f"Elapsed time: {finish_time - start_time}")
print("#"*20)
