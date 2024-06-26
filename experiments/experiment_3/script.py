"""
Gather the ONTs in a GPON board and
save the results in a CSV file.
"""
import csv

from netmiko import ConnectHandler
from ntc_templates.parse import parse_output

FILENAME = "results.csv"
BOARD_COMMAND = "display board 0"
BASE_ONT_COMMAND = "display ont info 0"
PLATFORM = "huawei_smartax"

CREDENTIALS = {
    "host": "localhost",
    "username": "admin",
    "password": "admin",
    "device_type": PLATFORM,
    "port": 6000
}

GPON_BOARDS: dict[str, int] = {
    'H901XGHDE': 8,
    'H901OGHK': 24,
    'H901NXED': 8,
    'H901OXHD': 8,
    'H902OXHD': 8,
    'H901GPSFE': 16,
    'H901OXEG': 24,
    'H901TWEDE': 8,
    'H901XSHF': 16,
    'H902GPHFE': 16,
}

def main():
    """ Main function """
    results = []

    with ConnectHandler(**CREDENTIALS) as conn:
        output = conn.send_command(BOARD_COMMAND)
        parsed_output = parse_output(platform=PLATFORM, command=BOARD_COMMAND, data=output)
        slot_id, n_ports = [(board["slot_id"], GPON_BOARDS[board["boardname"]])
                                for board in parsed_output
                                if board["boardname"] in GPON_BOARDS][0]
        for i in range(n_ports):
            command = f"{BASE_ONT_COMMAND} {slot_id} {i}"
            output = conn.send_command(command)
            result = parse_output(platform=PLATFORM, command=command, data=output)
            results.append(result)

    with open(FILENAME, "w", newline="\n", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(result[0].keys())
        writer.writerows([row.values() for result in results for row in result])

if __name__ == "__main__":
    main()
