import csv
import sys
import time
import resource
from fakenos import FakeNOS

replicas = int(sys.argv[2])

inventory = {
    "hosts": {
        "device": {
            "username": "admin",
            "password": "admin",
            "port": 6000,
            "platform": sys.argv[1], 
        }
    }
}

if replicas > 1:
    inventory["hosts"]["device"]["replicas"] = replicas
    inventory["hosts"]["device"]["port"] = [6000, 6000 + replicas - 1]


start_resources = resource.getrusage(resource.RUSAGE_SELF)
start_time = time.time()
with FakeNOS(inventory=inventory) as net:
    time.sleep(5)
end_time = time.time()
end_resources = resource.getrusage(resource.RUSAGE_SELF)
used_timed = end_time - start_time - 5
cpu_time = end_resources.ru_utime - start_resources.ru_utime
ram_usage = end_resources.ru_maxrss - start_resources.ru_maxrss
print(f"Platform: {sys.argv[1]}, CPU Time: {cpu_time:.2f}, RAM Usage: {ram_usage:.2f}")

with open(f'results/{sys.argv[1]}_{sys.argv[2]}.csv', 'a+', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow([cpu_time, ram_usage, used_timed])

