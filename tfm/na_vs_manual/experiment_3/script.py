"""
This script gather the registered ONTs in an OLT with 1 board in the slot 0.
"""
import csv
from netmiko import ConnectHandler
from ntc_templates.parse import parse_output

FILENAME = "results.csv"
BASE_COMMAND = "display ont info 0 0"
PLATFORM = "huawei_smartax"

CREDENTIALS = {
    "host": "localhost",
    "username": "user",
    "password": "user",
    "device_type": PLATFORM,
    "port": 6000
}

def main():
    """ Main function """
    results = []

    with ConnectHandler(**CREDENTIALS) as conn:
        for i in range(8):
            command = f"{BASE_COMMAND} {i}"
            output = conn.send_command(command)
            result = parse_output(platform=PLATFORM, command=command, data=output)
            results.append(result)

    with open(FILENAME, "w", newline="\n", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(result[0].keys())
        writer.writerows([row.values() for result in results for row in result])

if __name__ == "__main__":
    main()
