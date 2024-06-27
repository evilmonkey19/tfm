import os
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt

load_dotenv()

WPM_MANUAL_TYPEWRITER_5_MIN=os.getenv("WPM_MANUAL_TYPEWRITER_5_MIN")
WPM_MANUAL_TYPEWRITER_1_HOUR=os.getenv("WPM_MANUAL_TYPEWRITER_1_HOUR")
WPM_ELECTRONIC_TYPEWRITER=os.getenv("WPM_ELECTRONIC_TYPEWRITER")
MIN_CONNECTION_TIME=float(os.getenv("MIN_CONNECTION_TIME"))

na_results = pd.read_csv('na_results.csv')
na_results['time_duration'] = pd.to_timedelta(na_results['Time'])
na_results['total_seconds'] = na_results['time_duration'].dt.total_seconds()


time_typing = 0
with open('results.csv', 'r', encoding='utf-8') as file:
    script = file.read()
    words = script.split()
    time_typing_manual_5_min = len(words) / int(WPM_MANUAL_TYPEWRITER_5_MIN) * 60
    time_typing_manual_1_hour = len(words) / int(WPM_MANUAL_TYPEWRITER_1_HOUR) * 60
    time_typing_electronic = len(words) / int(WPM_ELECTRONIC_TYPEWRITER) * 60

time_typing_manual_5_min = time_typing_manual_5_min + MIN_CONNECTION_TIME
time_typing_manual_1_hour = time_typing_manual_1_hour + MIN_CONNECTION_TIME
time_typing_electronic = time_typing_electronic + MIN_CONNECTION_TIME

plt.plot(na_results['total_seconds'], label='Network Automation')

# plot a horizontal line representing the time taken by a human
plt.axhline(y=time_typing_manual_5_min, color='g', linestyle='--', label='World Guinness Record Manual Typewriter 5 min')
plt.axhline(y=time_typing_manual_1_hour, color='b', linestyle='--', label='World Guinness Record Manual Typewriter 1 hour')
plt.axhline(y=time_typing_electronic, color='y', linestyle='--', label='World Guinness Record Electronic Typewriter')

# Set the title and labels
plt.title("Gathering boards info using manual and network automation")
plt.xticks(range(0, 101, 10))
plt.xlabel('Experiment number')
plt.ylabel('Time (s)')

# Show the legend
plt.legend()

# Save the plot as SVG and PNG
plt.savefig('comparison.svg')
plt.savefig('comparison.png')

# Show the plot
plt.show()
