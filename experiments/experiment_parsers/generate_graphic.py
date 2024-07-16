import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

# Read the CSV file into a pandas DataFrame
df = pd.read_csv('results.csv')
df.drop(columns=['Unnamed: 0'], inplace=True)

# Calculate the average time for each vendor
average_time = df.mean()

plt.figure(figsize=(10, 6))
# Sort the average time and standard deviation in ascending order
average_time = average_time.sort_values(ascending=True)

# # Plot the bar graph with error bars
plt.barh(average_time.sort_values(ascending=True).index, average_time.sort_values(ascending=True).values)
plt.ylabel('Parsers')
plt.xlabel('Average Time')
plt.title('Average Time to parse an output')
plt.xticks(np.arange(0, 0.007, 0.0008))  # Set y-axis ticks to be in increments of 5
# # Add horizontal lines for each vertical line
for i in np.arange(0, 0.007, 0.0008):
    plt.axvline(x=i, color='gray', linestyle='dotted', alpha=0.2)
plt.tight_layout()
plt.subplots_adjust(left=0.2)
plt.savefig('parsers.png', dpi=300)
plt.show()
