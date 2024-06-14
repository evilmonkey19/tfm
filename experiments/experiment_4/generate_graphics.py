import pandas as pd
import matplotlib.pyplot as plt

# Read the CSV files
manual_results = pd.read_csv('manual_results.csv')
na_results = pd.read_csv('na_results.csv')

# Plot the data
plt.plot(manual_results['Time Taken'], label='Manual')
plt.plot(na_results['Time Taken'], label='Network Automation')

# Set the title and labels
plt.title("Gathering service states using manual and network automation")
plt.xticks(range(0, 10))
plt.xlabel('Experiment number')
plt.ylabel('Time (s)')

# Show the legend
plt.legend()

# Save the plot as SVG and PNG
plt.savefig('comparison.svg')
plt.savefig('comparison.png')

# Show the plot
plt.show()

plt.bar(range(len(manual_results)), manual_results["Number of mismatchs"], label="Manual")
plt.bar(range(len(na_results)), na_results["Number of mismatchs"], label="Network Automation")

plt.title("Number of mismatchs between manual and network automation")
plt.xticks(range(len(manual_results)))
plt.xlabel("Experiment number")
plt.ylabel("Number of mismatchs")

plt.legend()

plt.savefig("mismatchs.svg")
plt.savefig("mismatchs.png")

plt.show()