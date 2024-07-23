import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

tries = 10

na_results = pd.read_csv('results_detected_onts.csv')

sites = tuple(na_results['site_name'].unique())
mean_detected = na_results.groupby('site_name')['detected'].mean()
mean_real = na_results.groupby('site_name')['real'].mean()
mean_correct = na_results.groupby('site_name')['correct'].mean()

ind = np.arange(len(sites))

plt.figure(figsize=(10, 5))

width = 0.15

plt.bar(ind, mean_detected, width, label='Detected')
plt.bar(ind + width , mean_real, width, label='Real')
plt.bar(ind + width*2 , mean_correct, width, label='Correct')

plt.xlabel('Sites')
plt.ylabel('Values')
plt.title('Detected, Real and Correct')
plt.xticks(ind + width , sites)
plt.legend(loc='best')
# plt.show()

for site in sites:
    for _try in range(1, tries+1):
        misconfigurations_filename = f"misconfigurations_results_{site.replace('site_', '')}_{_try}.csv"
        if not os.path.isfile(misconfigurations_filename):
            continue
        new_lines = []
        with open(misconfigurations_filename, 'r') as f:
            lines = f.readlines()
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) < 4:
                    new_lines.append(line)
                    continue
                time_part = parts[2] + ":" + parts[3]
                event_part = parts[1]
                if 'unregistered' in event_part:
                    event_part = 'detected ' + event_part
                new_lines.append(parts[0] + ',' + event_part + ',' + time_part + '\n')
        with open("copy" + misconfigurations_filename, 'w') as f:
            f.writelines(new_lines)


import sys
sys.exit(0)

results = pd.DataFrame()

for site in sites:
    for _try in range(1,tries+1):
        misconfigurations_filename = f"misconfigurations_results_{site.replace('site_', '')}_{_try}.csv"
        chaos_monkey_filename = f"chaos_monkey_{site.replace('site_', '')}_try_{_try}.log"
        events = pd.DataFrame()
        if os.path.isfile(misconfigurations_filename):
            events = pd.read_csv(misconfigurations_filename)
            events['timestamp'] = pd.to_datetime(events['timestamp'], unit='ms')
            print(events)
            

print(results)