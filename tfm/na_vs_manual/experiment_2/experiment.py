"""
Check that services are correctly set up and the possible errors
compared to the manual configuration are correctly detected.
"""
import csv
import random
import time
import argparse

from fakenos import FakeNOS
from netmiko import ConnectHandler
from ntc_templates.parse import parse_output
import yaml

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("value", type=int)
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

values = None
with open("configurations/config_experiment.yaml", "r", encoding="utf-8") as file:
    values = yaml.safe_load(file.read())
    boards = values
    for board in values["frames"][0]["slots"]:
        if random.random() < 0.3:
            board = {
                "slotid": board["slotid"],
                "boardname": "",
                "status": "",
                "subtype0": "",
                "subtype1": "",
                "online_offline": ""
            }
        else:
            board["boardname"] = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890', k=8))
            board["status"] = random.choice(["Standby_failed", "Active", "Normal", "Active_normal", "Standby", "Failed", "Auto_find"])
            online_offline = ""
            if board["status"] not in ["Active_normal", "Auto_find"]:
                online_offline = random.choice(["online", "offline"])
            if random.random() < 0.1:
                board["subtype0"] = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890', k=4))
            if random.random() < 0.1:
                board["subtype1"] = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890', k=4))
    with open(f"configurations/config_experiment_{args.value}.yaml", "w", encoding="utf-8") as file:
        file.write(yaml.dump(values))


### NETWORK AUTOMATION ###
incorrect_boards = []
detected_boards = []
time_taken = 0
with FakeNOS(inventory=inventory) as net:
    start_time = time.time()
    with ConnectHandler(**credentials) as conn:
        COMMAND = "display board"
        output = conn.send_command(COMMAND)
        boards = parse_output(platform="huawei_smartax", command=COMMAND, data=output)
    time_taken = time.time() - start_time

number_of_mismatchs = 0
for real_board in values["frames"][0]["slots"]:
    checked_values_board = {
        "slot_id": str(real_board["slotid"]),
        "boardname": real_board["boardname"],
        "subtype_0": real_board.get("subtype0", ""),
        "subtype_1": real_board.get("subtype1", ""),
        "status": real_board.get("status", ""),
        "online_offline": real_board.get("online_offline", ""),
    }
    assert checked_values_board == boards[real_board["slotid"]], f"Real board: {checked_values_board}, Detected board: {boards[real_board['slotid']]}"

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

total_mismatchs = 0
# with open(f"manual_results/results_{args.value}.csv", "r", encoding="utf-8") as file, \
#     open(f"configurations/real/config_experiment_{args.value}.yaml", "r", encoding="utf-8") as real_file:
#     csv_reader = csv.reader(file, delimiter=',')
#     real_services = yaml.safe_load(real_file.read())["services"]
#     next(csv_reader)  # Skip the first row (titles)
#     for row, real_service in zip(csv_reader, real_services):
#         detected_service = {
#             "network_service": row[0],
#             "port": int(row[1]) if row[1] != "" else None,
#             "state": row[2]
#         }
#         if detected_service not in real_services:
#             total_mismatchs += 1
#             continue
#         if detected_service != real_service:
#             total_mismatchs += 1

# with open(f"manual_results.csv", "a+", encoding="utf-8") as file:
#     file.write(f"{total_mismatchs},{finish_time - start_time}\n")
        