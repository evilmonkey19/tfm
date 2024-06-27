"""
Gathers the running services in an OLT
and print out the results in a CSV file.
"""
import csv
import time
from netmiko import ConnectHandler
from ntc_templates.parse import parse_output
from fakenos import FakeNOS
import threading

FILENAME = "results.csv"
COMMAND = "display sysman service state"
PLATFORM = "huawei_smartax"
N_THREADS = 10
N_ROUNDS = 2

inventory = {
    "hosts": {
        "R": {
            "username": "user",
            "password": "user",
            "platform": "huawei_smartax",
        }
    }
}


def gather_data(cred, command, platform):
    with ConnectHandler(**cred) as conn:
        output = conn.send_command(command)
        parse_output(platform=platform, command=command, data=output)

threads = []
results = {
    i : [] for i in range (1, N_THREADS+1)
}
for round in range(1, N_ROUNDS+1):
    for i in range(1, N_THREADS+1):
        inventory["hosts"]["R"]["replicas"] = i + 1
        inventory["hosts"]["R"]["port"] = [6000, 6000 + i]
        credentials = []
        for replica in range(inventory["hosts"]["R"]["replicas"]):
            credentials.append({
                "host": "localhost",
                "username": inventory["hosts"]["R"]["username"],
                "password": inventory["hosts"]["R"]["password"],
                "device_type": inventory["hosts"]["R"]["platform"],
                "port": inventory["hosts"]["R"]["port"][0]+replica
            })
        with FakeNOS(inventory=inventory):
            start_time = time.time()
            for credential in credentials:
                thread = threading.Thread(gather_data(credential, COMMAND, PLATFORM))
                thread.start()
                threads.append(thread)

            for thread in threads:
                thread.join()
            threads.clear()
            results[i].append(time.time() - start_time)

with open(FILENAME, "w", newline="\n", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(results.keys())
    for i in range(len(results[1])):
        writer.writerow(result[i] for result in results.values())