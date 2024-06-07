import yaml
import sys

configurations = {}
with open(f"configurations/config_experiment_{sys.argv[1]}.yaml", "r") as f:
    configurations = yaml.safe_load(f)

onts = []
for frame_i, frame in enumerate(configurations["frames"]):
    for slot_i, slot in enumerate(frame["slots"]):
        if "ports" not in slot:
            continue
        for port_index, port in enumerate(slot["ports"]):
            for ont in port:
                ont_ = {
                    "fsp": f"{frame_i}/ {slot_i}/{port_index}",
                    "ont_id": str(ont['ont_id']),
                    "serial_number": ont['sn'],
                    "control_flag": ont['control_flag'],
                    "run_state": ont['run_state'],
                    "config_state": ont['config_state'], 
                    "match_state": ont['match_state'],
                    "protect_side": ont['protect_side'],
                    "description": ont['description'],
                }
                onts.append(ont_)


detected_onts = []
with open(f"manual_results/results_{sys.argv[1]}.csv", "r") as f:
    lines = f.readlines()
    for line in lines[1:]:
        row = line.split(",")
        ont = {
            "fsp": row[0],
            "ont_id": row[1],
            "serial_number": row[2],
            "control_flag": row[3],
            "run_state": row[4],
            "config_state": row[5],
            "match_state": row[6],
            "protect_side": row[7],
            "description": row[8].strip(),
        }
        detected_onts.append(ont)

number_of_mismatchs = 0
for real_ont in onts:
    matching_onts = [ont for ont in detected_onts if ont['fsp'] == real_ont['fsp'] and ont['ont_id'] == real_ont['ont_id']]
    
    if matching_onts:
        try:
            assert real_ont == matching_onts[0], f"Real ont: {real_ont}, Detected ont: {matching_onts[0]}"
        except AssertionError:
            number_of_mismatchs += 1
            print(f"Real ont: {real_ont}, Detected ont: {matching_onts[0]}")
    else:
        number_of_mismatchs += 1

print(number_of_mismatchs)
