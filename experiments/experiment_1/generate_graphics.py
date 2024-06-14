import os
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt

load_dotenv()

WORLD_RECORD_WPM=os.getenv("WORLD_RECORD_WPM")
MIN_CONNECTION_TIME=float(os.getenv("MIN_CONNECTION_TIME"))

na_results = pd.read_csv('na_results.csv')
na_results['time_duration'] = pd.to_timedelta(na_results['Time taken'])
na_results['total_seconds'] = na_results['time_duration'].dt.total_seconds()


time_typing = 0
with open('results.csv', 'r', encoding='utf-8') as file:
    script = file.read()
    words = script.split()
    time_typing = len(words) / int(WORLD_RECORD_WPM) * 60

human_time = time_typing + int(MIN_CONNECTION_TIME)

plt.plot(na_results['total_seconds'], label='Network Automation')

# plot a horizontal line representing the time taken by a human
plt.axhline(y=human_time, color='r', linestyle='--', label='Manual (Barbara Blackburn)')

# Set the title and labels
plt.title("Gathering service states using manual and network automation")
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
