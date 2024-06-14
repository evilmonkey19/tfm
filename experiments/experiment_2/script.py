"""
Gathers the boards in an OLT
and print out the results in a CSV file.
"""
import csv
from netmiko import ConnectHandler
from ntc_templates.parse import parse_output

FILENAME: str = "results.csv"
COMMAND: str = "display board 0"
PLATFORM: str = "huawei_smartax"

CREDENTIALS: dict[str, str|int] = {
    "host": "localhost",
    "username": "admin",
    "password": "admin",
    "device_type": PLATFORM,
    "port": 6000
}

def main():
    """ Main function """
    result = None

    with ConnectHandler(**CREDENTIALS) as conn:
        output = conn.send_command(COMMAND)
        result = parse_output(platform=PLATFORM, command=COMMAND, data=output)

    with open(FILENAME, "w", newline="\n", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(result[0].keys())
        writer.writerows([row.values() for row in result])

if __name__ == "__main__":
    main()
