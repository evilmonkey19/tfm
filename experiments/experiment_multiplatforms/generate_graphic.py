import pandas as pd

import matplotlib.pyplot as plt

# Read the CSV file into a pandas DataFrame
df = pd.read_csv('results.csv')

df = df.map(lambda x: x if x <= 30 else pd.NA)

# Calculate the average time for each vendor
average_time = df.mean()

# Calculate the standard deviation for each vendor
std_dev = df.std()

# Plot the bar graph with error bars
plt.barh(average_time.sort_values(ascending=True).index, average_time.sort_values(ascending=True).values, xerr=std_dev.sort_values(ascending=True).values, capsize=5)
plt.ylabel('Vendor')
plt.xlabel('Average Time')
plt.title('Average Time to access for each platform in Netmiko')
plt.xticks(range(0, 12, 1))  # Set y-axis ticks to be in increments of 5
# Add horizontal lines for each vertical line
for i in range(0,12,1):
    plt.axvline(x=i, color='gray', linestyle='dotted', alpha=0.2)
plt.tight_layout()
plt.subplots_adjust(left=0.2)
plt.savefig('results.png', dpi=300)
plt.savefig('results.svg', dpi=300)
plt.show()
