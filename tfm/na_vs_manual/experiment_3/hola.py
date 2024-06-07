import csv
import yaml

configurations = {}
with open(f"configurations/config_experiment_1.yaml", "r", encoding="utf-8") as file:
    configurations = yaml.safe_load(file)

detected_onts = []
with open(f"manual_results/results_1.csv", "r", encoding="utf-8") as file:
    csv_reader = csv.reader(file, delimiter=',')
    next(csv_reader)  # Skip the first row (titles)
    for row in csv_reader:
        ont = {
            "fsp": row[0],
            "ont_id": row[1],
            "serial_number": row[2],
            "control_flag": row[3],
            "run_state": row[4],
            "config_state": row[5],
            "match_state": row[6],
            "protect_side": row[7],
            "description": row[8],
        }
        detected_onts.append(ont)

checked_values_onts = []
for index, port in enumerate(configurations["frames"][0]["slots"][0]["ports"]):
    for ont in port:
        expected_ont = {
            'fsp': f'0/ 0/{index}',
            'ont_id': str(ont['ont_id']),
            'serial_number': ont['sn'],
            'control_flag': ont['control_flag'],
            'run_state': ont['run_state'],
            'config_state': ont['config_state'],
            'match_state': ont['match_state'],
            'protect_side': ont['protect_side'],
            'description': ont['description'],
        }
        checked_values_onts.append(expected_ont)

print(len(checked_values_onts))

number_of_mismatchs = 0
for real_ont in checked_values_onts:
    matching_onts = [ont for ont in detected_onts if ont['fsp'] == real_ont['fsp'] and ont['ont_id'] == real_ont['ont_id']]
    if matching_onts:
        try:
            assert real_ont == matching_onts[0], f"Real ont: {real_ont}, Detected ont: {matching_onts[0]}"
            # print(real_ont)
        except AssertionError:
            number_of_mismatchs += 1
            print(f"Real ont: {real_ont}, Detected ont: {matching_onts[0]}")
    else:
        number_of_mismatchs += 1
        # print(f"No matching ont found in detected_onts for real_ont: {real_ont}")
  
print(number_of_mismatchs)