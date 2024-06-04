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
checked_values_boards = [
    {
        "slot_id": str(board["slotid"]),
        "boardname": board["boardname"],
        "subtype_0": board.get("subtype0", ""),
        "subtype_1": board.get("subtype1", ""),
        "status": board.get("status", ""),
        "online_offline": board.get("online_offline", ""),
    }
    for board in values["frames"][0]["slots"]
]
for real_board in checked_values_boards:
    try:
        assert real_board == boards[int(real_board["slot_id"])], f"Real board: {real_board}, Detected board: {boards[int(real_board['slot_id'])]}"
    except AssertionError:
        number_of_mismatchs += 1
        print(f"Real board: {real_board}, Detected board: {boards[int(real_board['slot_id'])]}")

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
with open(f"manual_results/results_{args.value}.csv", "r", encoding="utf-8") as file:
    csv_reader = csv.reader(file, delimiter=',')
    next(csv_reader)  # Skip the first row (titles)
    for row in csv_reader:
        board = {
            "slot_id": row[0],
            "boardname": row[1],
            "status": row[2],
            "subtype_0": row[3],
            "subtype_1": row[4],
            "online_offline": row[5],
        }
        try:
            assert board == checked_values_boards[int(row[0])], f"Real board: {board}, Detected board: {checked_values_boards[int(row[0])]}"
        except AssertionError:
            total_mismatchs += 1
            print(f"Real board: {board}, Detected board: {checked_values_boards[int(row[0])]}")
            
with open(f"manual_results.csv", "a+", encoding="utf-8") as file:
    file.write(f"{total_mismatchs},{finish_time - start_time}\n")
        