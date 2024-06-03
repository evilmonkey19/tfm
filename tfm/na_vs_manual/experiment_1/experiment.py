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
            "configuration_file": f"configurations/real/config_experiment_{args.value}.yaml"
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

with open("configurations/real/config_experiment.yaml", "r", encoding="utf-8") as file:
    values = yaml.safe_load(file.read())
    for service in values["services"]:
        if service["network_service"] == 'ssh':
            continue
        if random.random() < 0.2:
            service["port"] = random.randint(0, 65535)
        service["state"] = random.choice(["enable", "disable"])
    with open(f"configurations/real/config_experiment_{args.value}.yaml", "w", encoding="utf-8") as file:
        file.write(yaml.dump(values))

with open("configurations/expected/expected_experiment.yaml", "r", encoding="utf-8") as file:
    values = yaml.safe_load(file.read())
    for service in values["services"]:
        if service["network_service"] == 'ssh':
            continue
        if random.random() < 0.2:
            service["port"] = random.randint(0, 65535)
        service["state"] = random.choice(["enable", "disable"])
    with open(f"configurations/expected/expected_experiment_{args.value}.yaml", "w", encoding="utf-8") as file:
        file.write(yaml.dump(values))


### NETWORK AUTOMATION ###
incorrect_services = []
time_taken = 0
with FakeNOS(inventory=inventory) as net:
    start_time = time.time()
    with ConnectHandler(**credentials) as conn:
        COMMAND = "display sysman service state"
        output = conn.send_command(COMMAND)
        services = parse_output(platform="huawei_smartax", command=COMMAND, data=output)
        for service in services:
            keys_to_update = {}
            for key, value in service.items():
                if value is not None and value.isdigit():
                    keys_to_update[key] = int(value)
                if value == "":
                    keys_to_update[key] = None
            service.update(keys_to_update)
        with open(f"configurations/expected/expected_experiment_{args.value}.yaml", "r", encoding="utf-8") as file:
            expected_output = yaml.safe_load(file.read())
        for expected_service in expected_output['services']:
            try:
                service = services[services.index(expected_service)]
                assert service == expected_service
            except (ValueError, AssertionError):
                incorrect_services.append(expected_service)
                continue
        time_taken = time.time() - start_time

number_of_mismatchs = 0
with open(f"configurations/expected/expected_experiment_{args.value}.yaml", "r", encoding="utf-8") as expect_file, \
        open(f"configurations/real/config_experiment_{args.value}.yaml", "r", encoding="utf-8") as real_file:
    real_services = yaml.safe_load(real_file.read())["services"]
    expect_services = yaml.safe_load(expect_file.read())["services"]
    correct_bad_mismatched_services = []
    for real_service, expect_service in zip(real_services, expect_services):
        if real_service != expect_service:
            correct_bad_mismatched_services.append(expect_service)
    if len(incorrect_services) != len(correct_bad_mismatched_services):
        is_okey = False
    for incorrect_service, correct_bad_mismatched_service in zip(incorrect_services, correct_bad_mismatched_services):
        if incorrect_service != correct_bad_mismatched_service:
            number_of_mismatchs += 1

with open(f"na_results.csv", "a+", encoding="utf-8") as file:
    file.write(f"{number_of_mismatchs},{time_taken}\n")


### MANUAL PART ###
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
with open(f"manual_results/results_1.csv", "r", encoding="utf-8") as file, \
    open(f"configurations/real/config_experiment_{args.value}.yaml", "r", encoding="utf-8") as real_file:
    csv_reader = csv.reader(file, delimiter=',')
    real_services = yaml.safe_load(real_file.read())["services"]
    next(csv_reader)  # Skip the first row (titles)
    for row, real_service in zip(csv_reader, real_services):
        detected_service = {
            "network_service": row[0],
            "port": int(row[1]) if row[1] != "" else None,
            "state": row[2]
        }
        if detected_service not in real_services:
            total_mismatchs += 1
            continue
        if detected_service != real_service:
            total_mismatchs += 1

with open(f"manual_results.csv", "a+", encoding="utf-8") as file:
    file.write(f"{total_mismatchs},{finish_time - start_time}\n")
        