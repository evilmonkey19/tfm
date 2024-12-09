import os
import csv
import datetime
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

tries = 10
n_sites = 10

#####################
# All ONTs detected #
#####################

na_results = pd.read_csv('results_detected_onts.csv')

sites = tuple(na_results['site_name'].unique())
mean_detected = na_results.groupby('site_name')['detected'].mean()
mean_real = na_results.groupby('site_name')['real'].mean()
mean_correct = na_results.groupby('site_name')['correct'].mean()

ind = np.arange(len(sites))

plt.figure(figsize=(10, 5))

width = 0.15

plt.bar(ind, mean_detected, width, label='Detected')
plt.bar(ind + width, mean_real, width, label='Real')
plt.bar(ind + width*2, mean_correct, width, label='Correct')

plt.xlabel('Sites')
plt.ylabel('Number of ONTs')
plt.title('Detected, Real and Correct ONTs')
plt.xticks(ind + width, sites)
plt.legend(loc='best')
plt.savefig('figures/onts_detected.png')
plt.close()

#####################
# Misconfigurations #
#####################

chaos_monkey_patterns = [
    r'(Unregistering) ([A-Z0-9]{16}) from site_[0-9]{1,2}',
    r'Changing (c vlan|s vlan|snmp profile|gemport|vlan type) for ([A-Z0-9]{16}) from site_[0-9]{1,2}',
    r'Changing state of (\S+) from site_[0-9]{1,2}',
]

misconfigurations = []

for n_site in range(n_sites):
    misconfigurations.append([])
    for _try in range(1, tries+1):
        misconfigurations_filename = f"results_only_misconfigurations/event_log_{n_site+1}_{_try}_only_misconfigurations.csv"
        if not os.path.isfile(misconfigurations_filename):
            raise FileNotFoundError(f"File {misconfigurations_filename} not found")
        chaos_monkey_filename = f'results_only_misconfigurations/chaos_monkey_{n_site+1}_try_{_try}_only_misconfigurations.csv'
        if not os.path.isfile(chaos_monkey_filename):
            raise FileNotFoundError(f"File {chaos_monkey_filename} not found")
        misconfigurations[n_site].append([])
        with open(chaos_monkey_filename, 'r') as f:
            csv_reader = csv.reader(f)
            for row in csv_reader:
                if row[0] == "_" or row[1] == "Connection error":
                    continue
                misconfiguration_type, sn, service = None, None, None
                for pattern in chaos_monkey_patterns:
                    if pattern == chaos_monkey_patterns[-1]:
                        service = re.match(pattern, row[1]).group(1)
                        break
                    if re.match(pattern, row[1]):
                        misconfiguration_type = re.match(pattern, row[1]).group(1)
                        sn = re.match(pattern, row[1]).group(2)
                        break
                if misconfiguration_type is None and sn is None and service is None:
                    raise ValueError(f"Could not find the misconfiguration type and sn in the row {row[1]}")
                misconfigurations[n_site][_try-1].append({
                    'site': row[0],
                    'misconfiguration_type': misconfiguration_type,
                    'sn': sn,
                    'service': service,
                    'generated_timestamp': datetime.datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S_%f'),
                    'detected_timestamp': '',
                    'recovered_timestamp': '',
                })

        with open(misconfigurations_filename, 'r') as f:
            csv_reader = csv.DictReader(f)
            events = list(csv_reader)
            first_registered_event_time = datetime.datetime.strptime(events[0]['timestamp'], '%Y-%m-%d %H:%M:%S_%f')
            first_generated_event_time = misconfigurations[n_site][_try-1][0]['generated_timestamp']
            if first_generated_event_time > first_registered_event_time:
                raise ValueError(f"First generated event time {first_generated_event_time} is greater than first registered event time {first_registered_event_time}")
            if first_registered_event_time.minute - first_generated_event_time.minute > 10:
                raise ValueError(f"First registered event time {first_registered_event_time} is more than 10 minutes after first generated event time {first_generated_event_time}")
            hours_shift = first_registered_event_time.hour - first_generated_event_time.hour if first_registered_event_time.hour >= first_generated_event_time.hour else 24 + first_registered_event_time.hour - first_generated_event_time.hour
            generated_events = misconfigurations[n_site][_try-1]
            for generated_event in generated_events:
                detection = next((e for e in events 
                                  if e['sn'] == generated_event['sn'] and
                                  datetime.datetime.strptime(e['timestamp'], '%Y-%m-%d %H:%M:%S_%f') > generated_event['generated_timestamp'] and
                                  e['fixed_detected'] == 'detected' and
                                  e['site'] == generated_event["site"] and
                                  e['event_type'].replace("_", " ") == generated_event['misconfiguration_type']), None)
                if detection is None:
                    continue
                fixing = next((e for e in events if e['uuid'] == detection['uuid'] and e['timestamp'] != detection['timestamp']), None)
                if fixing is None:
                    continue
                generated_event.update({
                    'detected_timestamp': datetime.datetime.strptime(detection['timestamp'], '%Y-%m-%d %H:%M:%S_%f') - datetime.timedelta(hours=hours_shift),
                    'recovered_timestamp': datetime.datetime.strptime(fixing['timestamp'], '%Y-%m-%d %H:%M:%S_%f') - datetime.timedelta(hours=hours_shift),
                })

########################################
# Misconfigurations detected over time #
########################################
for site in range(n_sites):
    for _try in range(tries):
        _misconfigurations = [m for m in misconfigurations[site][_try] if m['detected_timestamp'] != '' and m['recovered_timestamp'] != '']
        if len(_misconfigurations) == 0:
            raise ValueError(f"No misconfigurations detected in site {site} try {_try}")
        misconfigurations_df = pd.DataFrame(_misconfigurations)
        misconfigurations_df['generated_timestamp'] = pd.to_datetime(misconfigurations_df['generated_timestamp'])
        misconfigurations_df['detected_timestamp'] = pd.to_datetime(misconfigurations_df['detected_timestamp'])
        misconfigurations_df['recovered_timestamp'] = pd.to_datetime(misconfigurations_df['recovered_timestamp'])
        reference_timestamp = misconfigurations_df['generated_timestamp'].min()
        misconfigurations_df['generated_timestamp'] = misconfigurations_df['generated_timestamp'] - reference_timestamp
        misconfigurations_df['detected_timestamp'] = misconfigurations_df['detected_timestamp'] - reference_timestamp
        misconfigurations_df['recovered_timestamp'] = misconfigurations_df['recovered_timestamp'] - reference_timestamp
        misconfigurations_df['generated_timestamp'] = misconfigurations_df['generated_timestamp'].dt.total_seconds()
        misconfigurations_df['detected_timestamp'] = misconfigurations_df['detected_timestamp'].dt.total_seconds()
        misconfigurations_df['recovered_timestamp'] = misconfigurations_df['recovered_timestamp'].dt.total_seconds()
        plt.figure(figsize=(10, 5))
        plt.xlabel('Time (seconds)')
        plt.ylabel('Number of misconfigurations')
        plt.title(f'Misconfigurations detected over time using {site} sites - try {_try}')
        # msisconfigurations detected over time. do it accumulative over time
        time = np.arange(0, misconfigurations_df['generated_timestamp'].max(), 1)
        detected = np.zeros(len(time))
        generated = np.zeros(len(time))
        recovered = np.zeros(len(time))
        for i, t in enumerate(time):
            generated[i] = len(misconfigurations_df[misconfigurations_df['generated_timestamp'] <= t])
            detected[i] = len(misconfigurations_df[misconfigurations_df['detected_timestamp'] <= t])
            recovered[i] = len(misconfigurations_df[misconfigurations_df['recovered_timestamp'] <= t])
        plt.plot(time, generated, label='Generated')
        plt.plot(time, detected, label='Detected')
        plt.plot(time, recovered, label='Recovered')
        plt.legend(loc='best')
        plt.show()