"""
Check that services are correctly set up and the possible errors
compared to the manual configuration are correctly detected.
"""
import time
import argparse

from fakenos import FakeNOS
from netmiko import ConnectHandler
from ntc_templates.parse import parse_output

from tfm.na_vs_manual.config_generator import generate_config

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("value", type=int, default=1)
args = arg_parser.parse_args()


inventory = {
    "hosts": {
        "OLT": {
            "username": "admin",
            "password": "admin",
            "port": 6000,
            "platform": "huawei_smartax",
            "configuration_file": f"configurations/config_experiment_{args.value}.yaml"
        }
    }
}

credentials = {
    "host": "localhost",
    "username": "admin",
    "password": "admin",
    "device_type": "huawei_smartax",
    "port": 6000
}

configurations = generate_config(f'configurations/config_experiment_{args.value}.yaml')

gpon_boards = {
    'H901XGHDE': 8,
    'H901OGHK': 48,
    'H901NXED': 8,
    'H901OXHD': 8,
    'H902OXHD': 8,
    'H901GPSFE': 16,
    'H901OXEG': 24,
    'H901TWEDE': 8,
    'H901XSHF': 16,
    'H902GPHFE': 16,
}

### NETWORK AUTOMATION ###
incorrect_boards = []
detected_onts = []
time_taken = 0
with FakeNOS(inventory=inventory) as net:
    start_time = time.time()
    with ConnectHandler(**credentials) as conn:
        COMMAND = "display board 0"
        output = conn.send_command(COMMAND)
        boards = parse_output(platform="huawei_smartax", command=COMMAND, data=output)
        n_ports = gpon_boards[boards[0]['boardname']]
        for i in range(n_ports):
            COMMAND = f"display ont info 0 0 {i}"
            output = conn.send_command(COMMAND)
            detected_onts.extend(parse_output(platform="huawei_smartax", command=COMMAND, data=output))
    time_taken = time.time() - start_time

for ont in detected_onts:
    ont['ont_id'] = int(ont['ont_id'])
    ont['description'] = ont['description'].strip()

number_of_mismatchs = 0
checked_values_onts = [
    {
        "fsp": f'0/ 0/{index}',
        "ont_id": ont.get("ont_id", ""),
        "serial_number": ont.get("sn", ""),
        "control_flag": ont.get("control_flag", ""),
        "run_state": ont.get("run_state", ""),
        "config_state": ont.get("config_state", ""),
        "match_state": ont.get("match_state", ""),
        "protect_side": ont.get("protect_side", ""),
        "description": ont.get("description", "").strip(),
    } for index, port in enumerate(configurations["frames"][0]["slots"][0]["ports"]) \
        for ont in port
]

checked_values_onts = [ont for ont in checked_values_onts if ont['ont_id'] is not None]


for real_ont in checked_values_onts:
    matching_onts = [ont for ont in detected_onts if ont['fsp'] == real_ont['fsp'] and ont['ont_id'] == real_ont['ont_id']]
    if matching_onts:
        try:
            assert real_ont == matching_onts[0], f"Real ont: {real_ont}, Detected ont: {matching_onts[0]}"
        except AssertionError:
            number_of_mismatchs += 1
            print(f"Real ont: {real_ont}, Detected ont: {matching_onts[0]}")
    else:
        number_of_mismatchs += 1
        print(f"No matching ont found in detected_onts for real_ont: {real_ont}")

with open(f"na_results.csv", "a+", encoding="utf-8") as file:
    file.write(f"{number_of_mismatchs},{time_taken}\n")

# ### MANUAL PART ###
start_time = 0
finish_time = 0
print("#"*20)
print("Starting manual part")
print("#"*20)
with FakeNOS(inventory=inventory) as net:
    start_time = time.time()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        pass
    finish_time = time.time()

number_of_mismatchs = 0
detected_onts = []
with open(f"manual_results/results_{args.value}.csv", "r", encoding="utf-8") as f:
    lines = f.readlines()
    for line in lines[1:]:
        row = line.split(",")
        ont = {
            "fsp": row[0],
            "ont_id": int(row[1]),
            "serial_number": row[2],
            "control_flag": row[3],
            "run_state": row[4],
            "config_state": row[5],
            "match_state": row[6],
            "protect_side": row[7],
            "description": row[8].strip(),
        }
        detected_onts.append(ont)

print(checked_values_onts[0])
print(detected_onts[0])
for real_ont in checked_values_onts:
    matching_onts = [ont for ont in detected_onts if ont['fsp'] == real_ont['fsp'] and ont['ont_id'] == real_ont['ont_id']]
    if matching_onts:
        try:
            assert real_ont == matching_onts[0], f"Real ont: {real_ont}, Detected ont: {matching_onts[0]}"
        except AssertionError:
            number_of_mismatchs += 1
    else:
        number_of_mismatchs += 1
  
with open(f"manual_results.csv", "a+", encoding="utf-8") as file:
    file.write(f"{number_of_mismatchs},{finish_time - start_time}\n")
        