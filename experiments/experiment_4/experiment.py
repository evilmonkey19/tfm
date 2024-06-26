"""
Register an ONT 
"""
import os
from timeit import default_timer as timer
from datetime import timedelta
import csv

from dotenv import load_dotenv
from fakenos import FakeNOS

from experiments.experiment_4.script import main
from experiments.config_generator import generate_config

from tfm.na_vs_manual.config_generator import generate_config

load_dotenv()

generate_config("configuration.yaml.j2")

rounds = int(os.getenv("ROUNDS"))

start, end = 0, 0
list_of_times = []

for i in range(rounds):
    inventory = {
        "hosts": {
            "OLT": {
                "username": "admin",
                "password": "admin",
                "port": 6000,
                "platform": "huawei_smartax",
                "configuration_file": "configuration.yaml.j2"
            }
        }
    }
    with FakeNOS(inventory=inventory) as net:
        start = timer()
        main()
        end = timer()
        list_of_times.append(timedelta(seconds=end-start))
        print(f"Try {i}: {timedelta(seconds=end-start)}")

    with open("na_results.csv", "w", newline="\n", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Time"])
        for time in list_of_times:
            writer.writerow([str(time)])