import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

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
plt.savefig('figures/onts_detected.png')
plt.close()

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
        with open(misconfigurations_filename, 'w') as f:
            f.writelines(new_lines)

results = pd.DataFrame()

for site in sites:
    for _try in range(1,tries+1):
        misconfigurations_filename = f"misconfigurations_results_{site.replace('site_', '')}_{_try}.csv"
        chaos_monkey_filename = f"chaos_monkey_{site.replace('site_', '')}_try_{_try}.log"
        events = pd.DataFrame()
        if os.path.isfile(misconfigurations_filename):
            events = pd.read_csv(misconfigurations_filename)
            events['timestamp'] = pd.to_datetime(events['timestamp'].str.replace(':', '.', regex=False), format='%Y-%m-%d %H.%M.%S.%f')
        else:
            continue
        if not os.path.isfile(chaos_monkey_filename):
            continue
        if os.path.isfile(chaos_monkey_filename):
            with open(chaos_monkey_filename, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    timestamp, action = line.strip().split(' - ')
                    if action == "Starting chaos monkey":
                        new_event = pd.DataFrame([{
                            'timestamp': pd.to_datetime(timestamp, format='%Y-%m-%d %H:%M:%S,%f'),
                            'event': 'chaos monkey start'
                        }])
                        events = pd.concat([events, new_event], ignore_index=True)
                    elif action == "Exiting chaos monkey":
                        new_event = pd.DataFrame([{
                            'timestamp': pd.to_datetime(timestamp, format='%Y-%m-%d %H:%M:%S,%f'),
                            'event': 'chaos monkey end'
                        }])
                        events = pd.concat([events, new_event], ignore_index=True)
                    elif 'successfully unregistered' in action:
                        new_event = pd.DataFrame([{
                            'site': action.split()[-1],
                            'timestamp': pd.to_datetime(timestamp, format='%Y-%m-%d %H:%M:%S,%f'),
                            'event': f'performed unregistered {action.split()[0]}'
                        }])
                        events = pd.concat([events, new_event], ignore_index=True)
                    elif 'Shutting down' in action:
                        if action.startswith('site'):
                            new_event = pd.DataFrame([{
                                'site': action.split(":")[0],
                                'timestamp': pd.to_datetime(timestamp, format='%Y-%m-%d %H:%M:%S,%f'),
                                'event': 'shutting down OLT'
                            }])
                        else:
                            _timestamp = pd.to_datetime(timestamp, format='%Y-%m-%d %H:%M:%S,%f')
                            two_sec_before_after = events[
                                (events['timestamp'] >= _timestamp - pd.Timedelta(seconds=5))
                                & (events['timestamp'] <= _timestamp + pd.Timedelta(seconds=5))
                            ]
                            two_sec_before_after = two_sec_before_after[two_sec_before_after['event'].str.contains('OLT not responding')]
                            if len(two_sec_before_after) == 0:
                                new_event = pd.DataFrame([{
                                    'timestamp': _timestamp,
                                    'event': 'shutting down OLT'
                                }])
                            else:
                                new_event = pd.DataFrame([{
                                    'site': two_sec_before_after['site'].values[0],
                                    'timestamp': _timestamp,
                                    'event': 'shutting down OLT'
                                }])
                        events = pd.concat([events, new_event], ignore_index=True)
                    elif 'Starting' in action:
                        if action.startswith('site'):
                            new_event = pd.DataFrame([{
                                'site': action.split(":")[0],
                                'timestamp': pd.to_datetime(timestamp, format='%Y-%m-%d %H:%M:%S,%f'),
                                'event': 'starting OLT'
                            }])
                        else:
                            _timestamp = pd.to_datetime(timestamp, format='%Y-%m-%d %H:%M:%S,%f')
                            two_sec_before_after = events[
                                (events['timestamp'] >= _timestamp - pd.Timedelta(seconds=5))
                                & (events['timestamp'] <= _timestamp + pd.Timedelta(seconds=5))
                            ]
                            two_sec_before_after = two_sec_before_after[two_sec_before_after['event'].str.contains('OLT up')]
                            if len(two_sec_before_after) == 0:
                                new_event = pd.DataFrame([{
                                    'timestamp': _timestamp,
                                    'event': 'starting OLT'
                                }])
                            else:
                                new_event = pd.DataFrame([{
                                    'site': two_sec_before_after['site'].values[0],
                                    'timestamp': _timestamp,
                                    'event': 'starting OLT'
                                }])
                        events = pd.concat([events, new_event], ignore_index=True)

        events = events.sort_values(by='timestamp')
        chaos_monkey_end_index = events[events['event'] == 'chaos monkey end'].index
        chaos_monkey_start_index = events[events['event'] == 'chaos monkey start'].index
        if len(chaos_monkey_end_index) > len(chaos_monkey_start_index):
            chaos_monkey_end_index = chaos_monkey_end_index[:-1]
        if len(chaos_monkey_end_index) < len(chaos_monkey_start_index):
            chaos_monkey_start_index = chaos_monkey_start_index[:-1]
        for start, end in zip(chaos_monkey_start_index, chaos_monkey_end_index):
            events.loc[start:end, 'chaos_monkey'] = True
        with pd.option_context("future.no_silent_downcasting", True):
            events['chaos_monkey'] = events['chaos_monkey'].fillna(False).infer_objects(copy=False)
        chaos_monkey_events = events[events['chaos_monkey']].copy()
        chaos_monkey_events.drop(columns=['chaos_monkey'], inplace=True)
        chaos_monkey_start = chaos_monkey_events[chaos_monkey_events['event'] == 'chaos monkey start']
        start_time = chaos_monkey_start['timestamp'].values[0]
        chaos_monkey_events['seconds_from_reference'] = (events['timestamp'] - start_time).dt.total_seconds()

        # compare the performed unregistered with the detected
        performed_unregistered = chaos_monkey_events[chaos_monkey_events['event'].str.contains('performed unregistered')]
        detected_unregistered = chaos_monkey_events[chaos_monkey_events['event'].str.contains('detected unregistered')]
        registered = chaos_monkey_events[chaos_monkey_events['event'].str.startswith('registered')]
        # recovery = chaos_monkey_events[chaos_monkey_events['event'].str.contains('recovery')]
        performed_unregistered = performed_unregistered.drop_duplicates(subset='event', keep='first')
        detected_unregistered = detected_unregistered.drop_duplicates(subset='event', keep='first')
        registered = registered.drop_duplicates(subset='event', keep='first')
        detected_sn = detected_unregistered['event'].str.split().str[-1].values

        performed_unregistered = performed_unregistered[performed_unregistered['seconds_from_reference'] <= 300]
        detected_unregistered = detected_unregistered[detected_unregistered['seconds_from_reference'] <= 300]
        registered = registered[registered['seconds_from_reference'] <= 300]
        performed_unregistered = performed_unregistered.sort_values(by='seconds_from_reference', ignore_index=True)
        detected_unregistered = detected_unregistered.sort_values(by='seconds_from_reference', ignore_index=True)
        registered = registered.sort_values(by='seconds_from_reference', ignore_index=True)

        results[f'{site.replace("site_", "")}_try_{_try}'] = {
            'performed_unregistered': performed_unregistered,
            'detected_unregistered': detected_unregistered,
            'registered': registered
        }
        plt.figure(figsize=(10, 5))
        plt.plot(performed_unregistered['seconds_from_reference'], performed_unregistered.index + 1, '--o', label='Generated')
        plt.plot(detected_unregistered['seconds_from_reference'], detected_unregistered.index + 1, '-o', label='Detected')
        plt.legend(loc='best')
        plt.xlabel('Time (s)')
        plt.ylabel('Total number of misconfigurations')
        plt.title('Detected misconfigurations over time')
        plt.xlim(0, 300)
        plt.savefig(f'figures/misconfigurations_{site.replace("site_", "")}_try_{_try}.png')
        plt.close()


# for each site get the number of misconfigurations generated and detected in each try
plt.figure(figsize=(10, 5))
result_to_plot_performed = []
result_to_plot_detected = []
for site in sites:
    performed_unregistered = None
    detected_unregistered = None
    for _try in range(1, tries+1):
        if not f'{site.replace("site_", "")}_try_{_try}' in results:
            continue
        performed_unregistered = pd.concat([performed_unregistered, results[f'{site.replace("site_", "")}_try_{_try}']['performed_unregistered']], ignore_index=True)
        detected_unregistered = pd.concat([detected_unregistered, results[f'{site.replace("site_", "")}_try_{_try}']['detected_unregistered']], ignore_index=True)
    if performed_unregistered is None or detected_unregistered is None:
        continue

    all_performed_unregistered = performed_unregistered.groupby('site').count()
    all_detected_unregistered = detected_unregistered.groupby('site').count()
    result_to_plot_performed.append(all_performed_unregistered['event'].sum())
    result_to_plot_detected.append(all_detected_unregistered['event'].sum())

width = 0.3

plt.bar(ind, result_to_plot_performed, width, label='Generated')
plt.bar(ind + width , result_to_plot_detected, width, label='Detected')

plt.xticks(ind + width / 2, sites)
plt.legend(loc='best')
plt.xlabel('Sites')
plt.ylabel('Total number of misconfigurations')
plt.title('Detected misconfigurations by number of sites')
plt.savefig('figures/misconfigifications_detected.png')
plt.close()


time_taken_to_register = []

for site in sites:
    for _try in range(1, tries+1):
        if not f'{site.replace("site_", "")}_try_{_try}' in results:
            continue
        detected_unregistered_df = results[f'{site.replace("site_", "")}_try_{_try}']['detected_unregistered']
        registered_df = results[f'{site.replace("site_", "")}_try_{_try}']['registered']

        detected_unregistered_df['event_id'] = detected_unregistered_df['event'].str.split().str[-1]
        registered_df['event_id'] = registered_df['event'].str.split().str[-1]

        merged_df = pd.merge(detected_unregistered_df, registered_df, on='event_id', suffixes=('_detected', '_registered'))

        merged_df['seconds_difference'] = merged_df['seconds_from_reference_registered'] - merged_df['seconds_from_reference_detected']

        print(merged_df[['event_id', 'seconds_difference']])
        time_taken_to_register.append(merged_df['seconds_difference'].values[0])

plt.figure(figsize=(10, 5))
sns.kdeplot(time_taken_to_register, color="blue", fill=True, common_norm=True)
plt.xlabel('Time (s)')
plt.ylabel('Probability')
plt.title('Probability of time taken to recover from misconfiguration')
plt.xticks(np.arange(8, 20, 1))
plt.savefig('figures/time_taken_to_register_frequency.png')
plt.close()




for site in sites:
    for _try in range(1, tries+1):
        misconfigurations_filename = f"misconfigurations_results_{site.replace('site_', '')}_{_try}_only_shutting_down.csv"
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
        with open(misconfigurations_filename, 'w') as f:
            f.writelines(new_lines)

for site in sites:
    for _try in range(1,tries+1):
        misconfigurations_filename = f"misconfigurations_results_{site.replace('site_', '')}_{_try}_only_shutting_down.csv"
        chaos_monkey_filename = f"chaos_monkey_{site.replace('site_', '')}_try_{_try}_only_shutting_down.log"
        events = pd.DataFrame()
        if os.path.isfile(misconfigurations_filename):
            events = pd.read_csv(misconfigurations_filename)
            events['timestamp'] = pd.to_datetime(events['timestamp'].str.replace(':', '.', regex=False), format='%Y-%m-%d %H.%M.%S.%f')
        else:
            continue
        if not os.path.isfile(chaos_monkey_filename):
            continue
        if os.path.isfile(chaos_monkey_filename):
            with open(chaos_monkey_filename, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    timestamp, action = line.strip().split(' - ')
                    if action == "Starting chaos monkey":
                        new_event = pd.DataFrame([{
                            'timestamp': pd.to_datetime(timestamp, format='%Y-%m-%d %H:%M:%S,%f'),
                            'event': 'chaos monkey start'
                        }])
                        events = pd.concat([events, new_event], ignore_index=True)
                    elif action == "Exiting chaos monkey":
                        new_event = pd.DataFrame([{
                            'timestamp': pd.to_datetime(timestamp, format='%Y-%m-%d %H:%M:%S,%f'),
                            'event': 'chaos monkey end'
                        }])
                        events = pd.concat([events, new_event], ignore_index=True)
                    elif 'successfully unregistered' in action:
                        new_event = pd.DataFrame([{
                            'site': action.split()[-1],
                            'timestamp': pd.to_datetime(timestamp, format='%Y-%m-%d %H:%M:%S,%f'),
                            'event': f'performed unregistered {action.split()[0]}'
                        }])
                        events = pd.concat([events, new_event], ignore_index=True)
                    elif 'Shutting down' in action:
                        if action.startswith('site'):
                            new_event = pd.DataFrame([{
                                'site': action.split(":")[0],
                                'timestamp': pd.to_datetime(timestamp, format='%Y-%m-%d %H:%M:%S,%f'),
                                'event': 'shutting down OLT'
                            }])
                        else:
                            _timestamp = pd.to_datetime(timestamp, format='%Y-%m-%d %H:%M:%S,%f')
                            two_sec_before_after = events[
                                (events['timestamp'] >= _timestamp - pd.Timedelta(seconds=5))
                                & (events['timestamp'] <= _timestamp + pd.Timedelta(seconds=5))
                            ]
                            two_sec_before_after = two_sec_before_after[two_sec_before_after['event'].str.contains('OLT not responding')]
                            if len(two_sec_before_after) == 0:
                                new_event = pd.DataFrame([{
                                    'timestamp': _timestamp,
                                    'event': 'shutting down OLT'
                                }])
                            else:
                                new_event = pd.DataFrame([{
                                    'site': two_sec_before_after['site'].values[0],
                                    'timestamp': _timestamp,
                                    'event': 'shutting down OLT'
                                }])
                        events = pd.concat([events, new_event], ignore_index=True)
                    elif 'Starting' in action:
                        if action.startswith('site'):
                            new_event = pd.DataFrame([{
                                'site': action.split(":")[0],
                                'timestamp': pd.to_datetime(timestamp, format='%Y-%m-%d %H:%M:%S,%f'),
                                'event': 'starting OLT'
                            }])
                        else:
                            _timestamp = pd.to_datetime(timestamp, format='%Y-%m-%d %H:%M:%S,%f')
                            two_sec_before_after = events[
                                (events['timestamp'] >= _timestamp - pd.Timedelta(seconds=5))
                                & (events['timestamp'] <= _timestamp + pd.Timedelta(seconds=5))
                            ]
                            two_sec_before_after = two_sec_before_after[two_sec_before_after['event'].str.contains('OLT up')]
                            if len(two_sec_before_after) == 0:
                                new_event = pd.DataFrame([{
                                    'timestamp': _timestamp,
                                    'event': 'starting OLT'
                                }])
                            else:
                                new_event = pd.DataFrame([{
                                    'site': two_sec_before_after['site'].values[0],
                                    'timestamp': _timestamp,
                                    'event': 'starting OLT'
                                }])
                        events = pd.concat([events, new_event], ignore_index=True)

        events = events.sort_values(by='timestamp')
        chaos_monkey_end_index = events[events['event'] == 'chaos monkey end'].index
        chaos_monkey_start_index = events[events['event'] == 'chaos monkey start'].index
        if len(chaos_monkey_end_index) > len(chaos_monkey_start_index):
            chaos_monkey_end_index = chaos_monkey_end_index[:-1]
        if len(chaos_monkey_end_index) < len(chaos_monkey_start_index):
            chaos_monkey_start_index = chaos_monkey_start_index[:-1]
        for start, end in zip(chaos_monkey_start_index, chaos_monkey_end_index):
            events.loc[start:end, 'chaos_monkey'] = True
        with pd.option_context("future.no_silent_downcasting", True):
            events['chaos_monkey'] = events['chaos_monkey'].fillna(False).infer_objects(copy=False)
        chaos_monkey_events = events[events['chaos_monkey']].copy()
        chaos_monkey_events.drop(columns=['chaos_monkey'], inplace=True)
        chaos_monkey_start = chaos_monkey_events[chaos_monkey_events['event'] == 'chaos monkey start']
        start_time = chaos_monkey_start['timestamp'].values[0]
        chaos_monkey_events['seconds_from_reference'] = (events['timestamp'] - start_time).dt.total_seconds()

        # compare the performed unregistered with the detected
        print(chaos_monkey_events)
        performed_shutdown = chaos_monkey_events[chaos_monkey_events['event'].str.contains('shutting down OLT')]
        detected_shutdown = chaos_monkey_events[chaos_monkey_events['event'].str.contains('OLT not responding')]

        performed_shutdown = performed_shutdown[performed_shutdown['seconds_from_reference'] <= 300]
        detected_shutdown = detected_shutdown[detected_shutdown['seconds_from_reference'] <= 300]
        performed_shutdown = performed_shutdown.sort_values(by='seconds_from_reference', ignore_index=True)
        detected_shutdown = detected_shutdown.sort_values(by='seconds_from_reference', ignore_index=True)

        plt.figure(figsize=(10, 5))
        plt.plot(performed_shutdown['seconds_from_reference'], performed_shutdown.index + 1, '--o', label='Generated')
        plt.plot(detected_shutdown['seconds_from_reference'], detected_shutdown.index + 1, '-o', label='Detected', alpha=0.8)
        plt.legend(loc='best')
        plt.xlabel('Time (s)')
        plt.ylabel('Total number of errors')
        plt.title('Detected errors over time')
        plt.xlim(0, 300)
        plt.savefig(f'figures/errors_{site.replace("site_", "")}_try_{_try}.png')
        plt.close()