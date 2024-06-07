"""
Check that services are correctly set up and the possible errors
compared to the manual configuration are correctly detected.
"""
import csv
import random
import time
import argparse
import string
from dataclasses import dataclass

from fakenos import FakeNOS
from netmiko import ConnectHandler
from ntc_templates.parse import parse_output
import yaml
from wonderwords import RandomSentence

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("value", type=int, default=1)
args = arg_parser.parse_args()

# @dataclass
# class Args:
#     value = 1

# args = Args()


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

gpon_boards = {
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

s = RandomSentence()


def get_random_mac():
    """ It generates a random mac-address in the format xxxx-xxxx-xxxx """
    mac_address: str = ''
    for _ in range(3):
        mac_address += ''.join(random.choices(string.hexdigits, k=4)) + '-'
    return mac_address[:-1].lower()

def get_ont_global_id():
    """ Get ont global id """
    next_global_id = 0
    while True:
        yield next_global_id
        next_global_id += 1

ont_global_id = get_ont_global_id()

ont_models = [
    'EchoLife EG8145V5',
    'EchoLife EG8247H5',
    'EchoLife EG8040H6',
    'OptiXstar EG8145X6-10'
    'OptiXstar EN8010Ts-20',
    'OptiXstar EG8010Hv6-10',
    'OptiXstar P871E',
    'OptiXstar P615E-L1',
    'OptiXstar P815E-L1',
    'OptiXstar P605E-L1',
    'OptiXstar P612E-E',
    'OptiXstar P805E-L1',
    'OptiXstar P802E',
    'OptiXstar P603E-E'
    'OptiXstar P613E-E',
    'OptiXstar P803E-E',
    'OptiXstar P813E-E',
    'OptiXstar P670E',
    'OptiXstar S600E',
    'OptiXstar S800E',
    'OptiXstar W826P',
    'OptiXstar W826E',
    'OptiXstar W626E-10',
]

ont_states = [
    {
        'config_state': 'normal',
        'match_state': 'match',
        'online_offline': 'online',
        'run_state': 'online',
        'control_flag': 'active',
        'protect_side': 'no',
    },
    {
        'config_state': 'initial',
        'match_state': 'initial',
        'online_offline': 'offline',
        'run_state': 'offline',
        'control_flag': 'active',
        'protect_side': 'no',
    },
    {
        'config_state': 'normal',
        'match_state': 'mismatch',
        'online_offline': 'online',
        'run_state': 'online',
        'control_flag': 'active',
        'protect_side': 'no',
    },
    {
        'config_state': '-',
        'match_state': '-',
        'online_offline': '-',
        'run_state': '-',
        'control_flag': 'active',
        'protect_side': 'yes',
    }
]

configurations: dict = {}
with open("configurations/config_experiment.yaml", "r", encoding="utf-8") as file:
    configurations = yaml.safe_load(file.read())

gpon_board = random.choice(list(gpon_boards))
configurations['frames'][0]['slots'] = [
    {
        'boardname': gpon_board,
        'online_offline': '',
        'slotid': 0,
        'status': 'Normal',
        'subtype0': '',
        'subtype1': '',
        'ports': [[
            {
                **random.choice(ont_states),
                'ont_id': i,
                'description': s.bare_bone_with_adjective(),
                'sn': ''.join(random.choices(string.ascii_uppercase + string.digits, k=16)),
                'registered': random.choice([True, False]),
                'is_epon': False,
                'oui_version': 'CTC3.0',
                'model': '240',
                'extended_model': 'HG8240',
                'nni_type': 'auto',
                'actual_nni_type': 'auto',
                'last_actual_nni_type': 'auto',
                'password': '0x303030303030303030300000000000000000000000000000000000000000000000000000(0000000000)',
                'loid': '000000000000000000000000',
                'checkcode': '000000000000',
                'vendor_id': 'HWTC',
                'version': 'MXU VER.A',
                'software_version': 'V8R017C00',
                'hardware_version': '140C4510',
                'equipment_id': "MXU",
                'customized_info': '',
                'mac': get_random_mac(),
                'equipment_sn': '',
                'multi-channel': 'Not support',
                'llid': '',
                'distance_m': random.randint(10, 90),
                'last_distance_m': random.randint(10, 90),
                'rtt_tq': '',
                'memory_occupation': random.randint(10, 90),
                'cpu_occupation': random.randint(10, 90),
                'temperature': random.randint(30,60),
                'authentic_type': 'MAC-auth',
                'management_mode': random.choices(['OMCI', 'OAM']),
                'software_work_mode': 'normal',
                'multicast_mode': 'IGMP-Snooping',
                'last_down_cause': 'dying-gasp',
                'type_d_support': 'Not support',
                'isolation_state': 'normal',
                'interoperability_mode': 'unknown',
                'fec_upstream_state': 'disable',
                'vs_id': 0,
                'vs_name': 'admin-vs',
                'global_ont_id': next(ont_global_id),
                'fiber_route': '',
                'line_profile_id': random.randint(0, 10),
                'line_profile_name': '',
            } for i in range(random.randint(1,32))
        ] for j in range(gpon_boards[gpon_board])]
    },
    {
        'boardname': '',
        'online_offline': '',
        'slotid': 1,
        'status': '',
        'subtype0': '',
        'subtype1': '',
    },
    {
        'boardname': '',
        'online_offline': '',
        'slotid': 2,
        'status': '',
        'subtype0': '',
        'subtype1': '',
    },
    {
        'boardname': random.choice(["H901PILA", "H901PISA", "H901PISB", "H902PISB"]),
        'online_offline': '',
        'slotid': 2,
        'status': 'Normal',
        'subtype0': '',
        'subtype1': '',
    },
    {
        'boardname': random.choice(['H902MPLAE', 'H901MPSCE']),
        'online_offline': '',
        'slotid': 3,
        'status': 'Normal',
        'subtype0': 'CPCF',
        'subtype1': '',
    },
    {
        'boardname': random.choice(['H901MPSCE', 'H902MPLAE']),
        'online_offline': 'Offline',
        'slotid': 4,
        'status': 'Standby_failed',
        'subtype0': 'CPCF',
        'subtype1': '',
    },
    {
        'boardname': '',
        'online_offline': '',
        'slotid': 5,
        'status': '',
        'subtype0': '',
        'subtype1': '',
    }
]

with open(f"configurations/config_experiment_{args.value}.yaml", "w", encoding="utf-8") as file:
    file.write(yaml.dump(configurations))


### NETWORK AUTOMATION ###
incorrect_boards = []
detected_onts = []
time_taken = 0
with FakeNOS(inventory=inventory) as net:
    start_time = time.time()
    with ConnectHandler(**credentials) as conn:
        COMMAND = "display board 0"
        output = conn.send_command(COMMAND)
        boards = parse_output(platform="huawei_smartax", command=COMMAND, data=output)
        n_ports = gpon_boards[boards[0]['boardname']]
        for i in range(n_ports):
            COMMAND = f"display ont info 0 0 {i}"
            output = conn.send_command(COMMAND)
            detected_onts.extend(parse_output(platform="huawei_smartax", command=COMMAND, data=output))
    time_taken = time.time() - start_time

for ont in detected_onts:
    ont['ont_id'] = int(ont['ont_id'])
    ont['description'] = ont['description'].strip()

number_of_mismatchs = 0
checked_values_onts = [
    {
        "fsp": f'0/ 0/{index}',
        "ont_id": ont.get("ont_id", ""),
        "serial_number": ont.get("sn", ""),
        "control_flag": ont.get("control_flag", ""),
        "run_state": ont.get("run_state", ""),
        "config_state": ont.get("config_state", ""),
        "match_state": ont.get("match_state", ""),
        "protect_side": ont.get("protect_side", ""),
        "description": ont.get("description", "").strip(),
    } for index, port in enumerate(configurations["frames"][0]["slots"][0]["ports"]) \
        for ont in port
]


for real_ont in checked_values_onts:
    matching_onts = [ont for ont in detected_onts if ont['fsp'] == real_ont['fsp'] and ont['ont_id'] == real_ont['ont_id']]
    if matching_onts:
        try:
            assert real_ont == matching_onts[0], f"Real ont: {real_ont}, Detected ont: {matching_onts[0]}"
        except AssertionError:
            number_of_mismatchs += 1
            print(f"Real ont: {real_ont}, Detected ont: {matching_onts[0]}")
    else:
        number_of_mismatchs += 1
        print(f"No matching ont found in detected_onts for real_ont: {real_ont}")

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

number_of_mismatchs = 0
detected_onts = []
with open(f"manual_results/results_{args.value}.csv", "r", encoding="utf-8") as f:
    lines = f.readlines()
    for line in lines[1:]:
        row = line.split(",")
        ont = {
            "fsp": row[0],
            "ont_id": int(row[1]),
            "serial_number": row[2],
            "control_flag": row[3],
            "run_state": row[4],
            "config_state": row[5],
            "match_state": row[6],
            "protect_side": row[7],
            "description": row[8].strip(),
        }
        detected_onts.append(ont)

print(checked_values_onts[0])
print(detected_onts[0])
for real_ont in checked_values_onts:
    matching_onts = [ont for ont in detected_onts if ont['fsp'] == real_ont['fsp'] and ont['ont_id'] == real_ont['ont_id']]
    if matching_onts:
        try:
            assert real_ont == matching_onts[0], f"Real ont: {real_ont}, Detected ont: {matching_onts[0]}"
        except AssertionError:
            number_of_mismatchs += 1
    else:
        number_of_mismatchs += 1
  
with open(f"manual_results.csv", "a+", encoding="utf-8") as file:
    file.write(f"{number_of_mismatchs},{finish_time - start_time}\n")
        