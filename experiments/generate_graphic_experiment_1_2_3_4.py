import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

WPM_MANUAL_TYPEWRITER_5_MIN = 176
WPM_MANUAL_TYPEWRITER_1_HOUR = 147
WPM_ELECTRONIC_TYPEWRITER = 216

# Read the CSV file into a pandas DataFrame
df_1 = pd.read_csv('experiment_1/na_results.csv')
df_2 = pd.read_csv('experiment_2/na_results.csv')
df_3 = pd.read_csv('experiment_3/na_results.csv')
df_4 = pd.read_csv('experiment_4/na_results.csv')

df_1['time_duration'] = pd.to_timedelta(df_1['Time'])
df_1['total_seconds'] = df_1['time_duration'].dt.total_seconds()

df_2['time_duration'] = pd.to_timedelta(df_2['Time'])
df_2['total_seconds'] = df_2['time_duration'].dt.total_seconds()

df_3['time_duration'] = pd.to_timedelta(df_3['Time'])
df_3['total_seconds'] = df_3['time_duration'].dt.total_seconds()

df_4['time_duration'] = pd.to_timedelta(df_4['Time'])
df_4['total_seconds'] = df_4['time_duration'].dt.total_seconds()

time_typing_manual_5_min = []
time_typing_manual_1_hour = []
time_typing_electronic = []

with open('experiment_1/results.csv', 'r', encoding='utf-8') as file:
    script = file.read()
    words = script.split()
    time_typing_manual_5_min.append(len(words) / WPM_MANUAL_TYPEWRITER_5_MIN * 60)
    time_typing_manual_1_hour.append(len(words) / WPM_MANUAL_TYPEWRITER_1_HOUR * 60)
    time_typing_electronic.append(len(words) / WPM_ELECTRONIC_TYPEWRITER * 60)

with open('experiment_2/results.csv', 'r', encoding='utf-8') as file:
    script = file.read()
    words = script.split()
    time_typing_manual_5_min.append(len(words) / WPM_MANUAL_TYPEWRITER_5_MIN * 60)
    time_typing_manual_1_hour.append(len(words) / WPM_MANUAL_TYPEWRITER_1_HOUR * 60)
    time_typing_electronic.append(len(words) / WPM_ELECTRONIC_TYPEWRITER * 60)

with open('experiment_3/results.csv', 'r', encoding='utf-8') as file:
    script = file.read()
    words = script.split()
    time_typing_manual_5_min.append(len(words) / WPM_MANUAL_TYPEWRITER_5_MIN * 60)
    time_typing_manual_1_hour.append(len(words) / WPM_MANUAL_TYPEWRITER_1_HOUR * 60)
    time_typing_electronic.append(len(words) / WPM_ELECTRONIC_TYPEWRITER * 60)

with open('experiment_4/results.csv', 'r', encoding='utf-8') as file:
    script = file.read()
    words = script.split()
    time_typing_manual_5_min.append(len(words) / WPM_MANUAL_TYPEWRITER_5_MIN * 60)
    time_typing_manual_1_hour.append(len(words) / WPM_MANUAL_TYPEWRITER_1_HOUR * 60)
    time_typing_electronic.append(len(words) / WPM_ELECTRONIC_TYPEWRITER * 60)

avg_time_1 = df_1['total_seconds'].mean()
avg_time_2 = df_2['total_seconds'].mean()
avg_time_3 = df_3['total_seconds'].mean()
avg_time_4 = df_4['total_seconds'].mean()
std_dev_1 = df_1['total_seconds'].std()
std_dev_2 = df_2['total_seconds'].std()
std_dev_3 = df_3['total_seconds'].std()
std_dev_4 = df_4['total_seconds'].std()

manual_typing_5_min = [time for time in time_typing_manual_5_min]
manual_typing_1_hour = [time for time in time_typing_manual_1_hour]
manual_typing_electronic = [time for time in time_typing_electronic]

print('Task 1: Network Automation')
print('Mean:', avg_time_1)
print('Standard Deviation:', std_dev_1)
print('Manual Typing 5 min:', manual_typing_5_min[0])
print('Manual Typing 1 hour:', manual_typing_1_hour[0])
print('Electronic Typing:', manual_typing_electronic[0])
print("#"*50)
print('Task 2: Network Automation')
print('Mean:', avg_time_2)
print('Standard Deviation:', std_dev_2)
print('Manual Typing 5 min:', manual_typing_5_min[1])
print('Manual Typing 1 hour:', manual_typing_1_hour[1])
print('Electronic Typing:', manual_typing_electronic[1])
print("#"*50)
print('Task 3: Network Automation')
print('Mean:', avg_time_3)
print('Standard Deviation:', std_dev_3)
print('Manual Typing 5 min:', manual_typing_5_min[2])
print('Manual Typing 1 hour:', manual_typing_1_hour[2])
print('Electronic Typing:', manual_typing_electronic[2])
print("#"*50)
print('Task 4: Network Automation')
print('Mean:', avg_time_4)
print('Standard Deviation:', std_dev_4)
print('Manual Typing 5 min:', manual_typing_5_min[3])
print('Manual Typing 1 hour:', manual_typing_1_hour[3])
print('Electronic Typing:', manual_typing_electronic[3])



# Plotting the vertical bars with mean time
experiment_labels = ['Task 1', 'Task 2', 'Task 3', 'Task 4']
mean_times = [avg_time_1, avg_time_2, avg_time_3, avg_time_4]
std_devs = [std_dev_1, std_dev_2, std_dev_3, std_dev_4]

### Plotting network automation tasks ###
plt.bar(experiment_labels, mean_times, yerr=std_devs, label='Network Automation')
plt.errorbar(experiment_labels, mean_times, yerr=std_devs, fmt='o', color='red')

plt.title('Time taken using Network Automation to perform the tasks')
plt.ylabel('Time (s)')
plt.show()

### Plotting All together ###
BAR_WIDTH = 0.2
fig, ax = plt.subplots(figsize=(12, 8))
x = np.arange(len(experiment_labels))

b1 = ax.bar(x, mean_times, BAR_WIDTH, label='Network Automation')
b2 = plt.bar(x+BAR_WIDTH, manual_typing_5_min, BAR_WIDTH, label='Manual 5 min')
b3 = plt.bar(x+BAR_WIDTH*2, manual_typing_1_hour, BAR_WIDTH, label='Manual 1 hour')
b4 = plt.bar(x+BAR_WIDTH*3, manual_typing_electronic, BAR_WIDTH, label='Electronic')
ax.set_xticks(x + BAR_WIDTH * 1.5 )
ax.set_xticklabels(experiment_labels)
ax.set_ylabel('Time (s)')
ax.legend()
plt.title('Network Automation vs. Manual Typing')

plt.yscale('log')  # Set y-axis to logarithmic scale

plt.show()

### Task 1 & 2 ###
BAR_WIDTH = 0.1
fig, ax = plt.subplots(figsize=(12, 8))
x = np.arange(len(experiment_labels[0:2]))

b1 = ax.bar(x, mean_times[0:2], BAR_WIDTH, label='Network Automation')
b2 = plt.bar(x+BAR_WIDTH, manual_typing_5_min[0:2], BAR_WIDTH, label='Manual 5 min')
b3 = plt.bar(x+BAR_WIDTH*2, manual_typing_1_hour[0:2], BAR_WIDTH, label='Manual 1 hour')
b4 = plt.bar(x+BAR_WIDTH*3, manual_typing_electronic[0:2], BAR_WIDTH, label='Electronic')
ax.set_xticks(x + BAR_WIDTH * 1.5 )
ax.set_xticklabels(experiment_labels[0:2])
ax.set_ylabel('Time (s)')
ax.legend()
plt.title('Network Automation vs. Manual Typing (Task 1 & 2)')


plt.show()

### Task 3 & 4 ###
BAR_WIDTH = 0.1
fig, ax = plt.subplots(figsize=(12, 8))
x = np.arange(len(experiment_labels[2:]))
b1 = ax.bar(x, mean_times[2:3], BAR_WIDTH, label='Network Automation')
b2 = plt.bar(x+BAR_WIDTH, manual_typing_5_min[2:], BAR_WIDTH, label='Manual 5 min')
b3 = ax.bar(x+BAR_WIDTH*2, manual_typing_1_hour[2:], BAR_WIDTH, label='Manual 1 hour')
b4 = ax.bar(x+BAR_WIDTH*3, manual_typing_electronic[2:], BAR_WIDTH, label='Electronic')
ax.set_xticks(x + BAR_WIDTH * 1.5 )
ax.set_xticklabels(experiment_labels[2:])
ax.set_ylabel('Time (s)')
ax.legend()
plt.title('Network Automation vs. Manual Typing (Task 3 & 4)')
plt.yscale('log')

plt.show()