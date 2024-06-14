"""
Check that services are correctly set up and the possible errors
compared to the manual configuration are correctly detected.
"""
import time
import argparse
from dataclasses import dataclass

from fakenos import FakeNOS
from netmiko import ConnectHandler
from ntc_templates.parse import parse_output
from ttp import ttp

from tfm.na_vs_manual.config_generator import generate_config

# arg_parser = argparse.ArgumentParser()
# arg_parser.add_argument("value", type=int, default=1)
# args = arg_parser.parse_args()

@dataclass
class Args:
    value: int

args = Args(value=1)


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

configurations = generate_config(f'configurations/config_experiment_{args.value}.yaml')

### NETWORK AUTOMATION ###
registered_onts = []
time_taken = 0
ending_configurations = None

def command_response(conn, command):
    output = conn.send_command(command)
    return parse_output(platform="huawei_smartax", command=command, data=output)

with FakeNOS(inventory=inventory) as net:
    time.sleep(5)
    start_time = time.time()
    with ConnectHandler(**credentials) as conn:
        conn.enable()
        conn.config_mode()
        conn.send_command("ont-srvprofile gpon profile-id 500 profile-name new_link", auto_find_prompt=False)
        conn.find_prompt()
        conn.send_command("ont-port pots 4 eth 4")
        response = command_response(conn, "port vlan eth1 500")
        if int(response[0]["failed"]) != 0:
            raise Exception("Failed to set port vlan")
        conn.send_command("commit")
        conn.send_command("quit", auto_find_prompt=False)
        conn.find_prompt()
        conn.send_command("ont-lineprofile gpon profile-id 500 profile-name new_link", auto_find_prompt=False)
        conn.find_prompt()
        conn.send_command("tcont 4 dba-profile-id 5")
        conn.send_command("gem add 126 eth tcont 4")
        conn.send_command("gem mapping 126 0 vlan 500")
        conn.send_command("commit")
        conn.send_command("quit", auto_find_prompt=False)
        conn.find_prompt()
        conn.send_command("interface gpon 0/0", auto_find_prompt=False)
        conn.find_prompt()
        onts = command_response(conn, "display ont autofind 6")
        for ont in onts:
            ont_sn = ont.get("serial_number", "").split(" ")[0]
            response = command_response(conn, f"ont add 6 sn-auth {ont_sn} omci ont-lineprofile-id 500 ont-srvprofile-id 500 desc {ont_sn}")
            command = f"display ont info {response[0]['port_id']} {response[0]['ont_id']}"
            output = conn.send_command(command)
            parsed_output = parse_output(platform="huawei_smartax", command=command, data=output)
            # Parsing Tramas GEM
            parser = ttp(data=output, template="getting_gems.ttp")
            parser.parse()
            tconts = parser.result()[0][0]["tconts"]
            fields_to_register = ["fsp", "ont_id", "control_flag",
                               "run_state", "match_state", "management_mode",
                               "authentic_type", "serial_number", "description",
                               "line_profile_id", "line_profile_name",
                               "service_profile_id", "service_profile_name",
                               "number_pots", "number_eth", "number_tdm", "number_moca", "number_catv"]
            registered_ont = {field: parsed_output[0].get(field, None) for field in fields_to_register}
            registered_ont.update({"tconts": tconts})
            registered_onts.append(registered_ont)
        conn.send_command("quit", auto_find_prompt=False)
        conn.find_prompt()
    
    time_taken = time.time() - start_time
    ending_configurations = net.hosts["OLT"].nos.device.configurations

### CHECKING NETWORK AUTOMATION RESULTS ###
for real_ont in configurations["frames"][0]["slots"][0]["ports"][0]:
    pass

    # end_configurations = net.hosts["OLT"].nos.device.configurations
#         n_ports = gpon_boards[boards[0]['boardname']]
#         for i in range(n_ports):
#             COMMAND = f"display ont info 0 0 {i}"
#             output = conn.send_command(COMMAND)
#             detected_onts.extend(parse_output(platform="huawei_smartax", command=COMMAND, data=output))
#     time_taken = time.time() - start_time

# for ont in detected_onts:
#     ont['ont_id'] = int(ont['ont_id'])
#     ont['description'] = ont['description'].strip()

# number_of_mismatchs = 0
# checked_values_onts = [
#     {
#         "fsp": f'0/ 0/{index}',
#         "ont_id": ont.get("ont_id", ""),
#         "serial_number": ont.get("sn", ""),
#         "control_flag": ont.get("control_flag", ""),
#         "run_state": ont.get("run_state", ""),
#         "config_state": ont.get("config_state", ""),
#         "match_state": ont.get("match_state", ""),
#         "protect_side": ont.get("protect_side", ""),
#         "description": ont.get("description", "").strip(),
#     } for index, port in enumerate(configurations["frames"][0]["slots"][0]["ports"]) \
#         for ont in port
# ]

# checked_values_onts = [ont for ont in checked_values_onts if ont['ont_id'] is not None]


# for real_ont in checked_values_onts:
#     matching_onts = [ont for ont in detected_onts if ont['fsp'] == real_ont['fsp'] and ont['ont_id'] == real_ont['ont_id']]
#     if matching_onts:
#         try:
#             assert real_ont == matching_onts[0], f"Real ont: {real_ont}, Detected ont: {matching_onts[0]}"
#         except AssertionError:
#             number_of_mismatchs += 1
#             print(f"Real ont: {real_ont}, Detected ont: {matching_onts[0]}")
#     else:
#         number_of_mismatchs += 1
#         print(f"No matching ont found in detected_onts for real_ont: {real_ont}")

# with open(f"na_results.csv", "a+", encoding="utf-8") as file:
#     file.write(f"{number_of_mismatchs},{time_taken}\n")

# # ### MANUAL PART ###
# start_time = 0
# finish_time = 0
# print("#"*20)
# print("Starting manual part")
# print("#"*20)
# with FakeNOS(inventory=inventory) as net:
#     start_time = time.time()
#     try:
#         while True:
#             pass
#     except KeyboardInterrupt:
#         pass
#     finish_time = time.time()

# number_of_mismatchs = 0
# detected_onts = []
# with open(f"manual_results/results_{args.value}.csv", "r", encoding="utf-8") as f:
#     lines = f.readlines()
#     for line in lines[1:]:
#         row = line.split(",")
#         ont = {
#             "fsp": row[0],
#             "ont_id": int(row[1]),
#             "serial_number": row[2],
#             "control_flag": row[3],
#             "run_state": row[4],
#             "config_state": row[5],
#             "match_state": row[6],
#             "protect_side": row[7],
#             "description": row[8].strip(),
#         }
#         detected_onts.append(ont)

# print(checked_values_onts[0])
# print(detected_onts[0])
# for real_ont in checked_values_onts:
#     matching_onts = [ont for ont in detected_onts if ont['fsp'] == real_ont['fsp'] and ont['ont_id'] == real_ont['ont_id']]
#     if matching_onts:
#         try:
#             assert real_ont == matching_onts[0], f"Real ont: {real_ont}, Detected ont: {matching_onts[0]}"
#         except AssertionError:
#             number_of_mismatchs += 1
#     else:
#         number_of_mismatchs += 1
  
# with open(f"manual_results.csv", "a+", encoding="utf-8") as file:
#     file.write(f"{number_of_mismatchs},{finish_time - start_time}\n")
        