import csv
import os
import time
from fakenos import FakeNOS
from netmiko import ConnectHandler
from fakenos.core.nos import available_platforms
import dotenv

dotenv.load_dotenv()

rounds = int(os.getenv("ROUNDS", 1))

credentials = {
    "username": "admin",
    "password": "admin",
    "port": 6000,
    "host": "localhost",
}

inventory = {
    "hosts": {
        "R1": {
            "username": "admin",
            "password": "admin",
            "port": 6000,
        }
    }
}

available_platforms = [platform for platform in available_platforms if platform != "yamaha"]
results = {platform: [] for platform in available_platforms}
for round in range(rounds):
    print(f"Round {round+1}/{rounds}")
    for platform in available_platforms:
        inventory["hosts"]["R1"]["platform"] = platform
        credentials["device_type"] = platform
        with FakeNOS(inventory) as net:
            time.sleep(1)
            conn = ConnectHandler(**credentials)
            print(f"Platform: {platform}")
            start_time = time.time()
            conn.send_command('enable', auto_find_prompt=False)
            results[platform].append(time.time() - start_time)
            print(f"Platform: {platform}, Time: {time.time()- start_time:.2f}")
            conn.disconnect()
    
with open(f"results.csv", "w", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(results.keys())
    for i in range(rounds):
        writer.writerow([results[platform][i] for platform in results])
        
    

