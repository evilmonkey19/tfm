import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

# Read the CSV file into a pandas DataFrame
alcatel_aos = pd.read_csv('results/alcatel_aos.csv')
alcatel_sros = pd.read_csv('results/alcatel_sros.csv')
allied_telesis_awplus = pd.read_csv('results/allied_telesis_awplus.csv')
arista_eos = pd.read_csv('results/arista_eos.csv')
aruba_os = pd.read_csv('results/aruba_os.csv')
avaya_ers = pd.read_csv('results/avaya_ers.csv')
avaya_vsp = pd.read_csv('results/avaya_vsp.csv')
broadcom_icos = pd.read_csv('results/broadcom_icos.csv')
brocade_netiron = pd.read_csv('results/brocade_netiron.csv')
checkpoint_gaia = pd.read_csv('results/checkpoint_gaia.csv')
cisco_asa = pd.read_csv('results/cisco_asa.csv')
cisco_ftd = pd.read_csv('results/cisco_ftd.csv')
cisco_ios = pd.read_csv('results/cisco_ios.csv')
cisco_nxos = pd.read_csv('results/cisco_nxos.csv')
cisco_s300 = pd.read_csv('results/cisco_s300.csv')
cisco_xr = pd.read_csv('results/cisco_xr.csv')
dell_force10 = pd.read_csv('results/dell_force10.csv')
dlink_ds = pd.read_csv('results/dlink_ds.csv')
eltex = pd.read_csv('results/eltex.csv')
ericsson_ipos = pd.read_csv('results/ericsson_ipos.csv')
extreme_exos = pd.read_csv('results/extreme_exos.csv')
hp_comware = pd.read_csv('results/hp_comware.csv')
hp_procurve = pd.read_csv('results/hp_procurve.csv')
huawei_smartax = pd.read_csv('results/huawei_smartax.csv')
huawei_vrp = pd.read_csv('results/huawei_vrp.csv')
ipinfusion_ocnos = pd.read_csv('results/ipinfusion_ocnos.csv')
juniper_junos = pd.read_csv('results/juniper_junos.csv')
linux = pd.read_csv('results/linux.csv')
ubiquiti_edgerouter = pd.read_csv('results/ubiquiti_edgerouter.csv')
ubiquiti_edgeswitch = pd.read_csv('results/ubiquiti_edgeswitch.csv')
vyatta_vyos = pd.read_csv('results/vyatta_vyos.csv')
zyxel_os = pd.read_csv('results/zyxel_os.csv')

results = {
    'alcatel_aos': alcatel_aos,
    'alcatel_sros': alcatel_sros,
    'allied_telesis_awplus': allied_telesis_awplus,
    'arista_eos': arista_eos,
    'aruba_os': aruba_os,
    'avaya_ers': avaya_ers,
    'avaya_vsp': avaya_vsp,
    'broadcom_icos': broadcom_icos,
    'brocade_netiron': brocade_netiron,
    'checkpoint_gaia': checkpoint_gaia,
    'cisco_asa': cisco_asa,
    'cisco_ftd': cisco_ftd,
    'cisco_ios': cisco_ios,
    'cisco_nxos': cisco_nxos,
    'cisco_s300': cisco_s300,
    'cisco_xr': cisco_xr,
    'dell_force10': dell_force10,
    'dlink_ds': dlink_ds,
    'eltex': eltex,
    'ericsson_ipos': ericsson_ipos,
    'extreme_exos': extreme_exos,
    'hp_comware': hp_comware,
    'hp_procurve': hp_procurve,
    'huawei_smartax': huawei_smartax,
    'huawei_vrp': huawei_vrp,
    'ipinfusion_ocnos': ipinfusion_ocnos,
    'juniper_junos': juniper_junos,
    'linux': linux,
    'ubiquiti_edgerouter': ubiquiti_edgerouter,
    'ubiquiti_edgeswitch': ubiquiti_edgeswitch,
    'vyatta_vyos': vyatta_vyos,
    'zyxel_os': zyxel_os,
}


### CPU Usage ###
# Calculate the average CPU usage for each vendor
average_cpu_usage = {}
for vendor, df in results.items():
    average_cpu_usage[vendor] = df['CPU time'].mean()

# Calculate the standard deviation for each vendor
std_dev_cpu_usage = {}
for vendor, df in results.items():
    std_dev_cpu_usage[vendor] = df['CPU time'].std()

# Plot the bar graph with error bars
plt.barh(
    [vendor.replace('_', ' ').title() for vendor in sorted(average_cpu_usage, key=average_cpu_usage.get)],
    [average_cpu_usage[vendor] for vendor in sorted(average_cpu_usage, key=average_cpu_usage.get)],
    xerr=[std_dev_cpu_usage[vendor] for vendor in sorted(average_cpu_usage, key=average_cpu_usage.get)],
    capsize=5
)
plt.ylabel('Vendor')
plt.xlabel('Average CPU Usage (%)')
plt.title('Average CPU Usage for each platform in FakeNOS')
plt.xticks(np.arange(0, 1, 0.1))  # Set y-axis ticks to be in increments of 10
# Add horizontal lines for each vertical line
for i in np.arange(0, 1, 0.1):
    plt.axvline(x=i, color='gray', linestyle='dotted', alpha=0.2)
plt.tight_layout()
plt.subplots_adjust(left=0.2)
plt.savefig('results_cpu_usage.png', dpi=300)
plt.savefig('results_cpu_usage.svg', dpi=300)
plt.show()

### Memory Usage ###
# Calculate the average memory usage for each vendor
average_memory_usage = {}
for vendor, df in results.items():
    average_memory_usage[vendor] = df[' RAM usage'].mean() / 1024 / 1024

# Calculate the standard deviation for each vendor
std_dev_memory_usage = {}
for vendor, df in results.items():
    std_dev_memory_usage[vendor] = df[' RAM usage'].std() / 1024 / 1024

# Plot the bar graph with error bars
plt.barh(
    [vendor.replace('_', ' ').title() for vendor in sorted(average_memory_usage, key=average_memory_usage.get)],
    [average_memory_usage[vendor] for vendor in sorted(average_memory_usage, key=average_memory_usage.get)],
    xerr=[std_dev_memory_usage[vendor] for vendor in sorted(average_memory_usage, key=average_memory_usage.get)],
    capsize=5
)
plt.ylabel('Vendor')
plt.xlabel('Average Memory Usage (MB)')
plt.title('Average Memory Usage for each platform in FakeNOS')
plt.xticks(np.arange(0, 20, 1))  # Set y-axis ticks to be in increments of 50
# Add horizontal lines for each vertical line
for i in np.arange(0, 20, 1):
    plt.axvline(x=i, color='gray', linestyle='dotted', alpha=0.2)
plt.tight_layout()
plt.subplots_adjust(left=0.2)
plt.savefig('results_memory_usage.png', dpi=300)
plt.savefig('results_memory_usage.svg', dpi=300)

plt.show()

### Time to Access ###
# Calculate the average time to access for each vendor
average_time = {}
for vendor, df in results.items():
    average_time[vendor] = df[' Time taken'].mean()

# Calculate the maximum time for each vendor
max_time = {}
for vendor, df in results.items():
    max_time[vendor] = df[' Time taken'].max()

# Calculate the minimum time for each vendor
min_time = {}
for vendor, df in results.items():
    min_time[vendor] = df[' Time taken'].min()

# Plot the bar graph with maximum, minimum, and average indicators
plt.barh(
    [vendor.replace('_', ' ').title() for vendor in sorted(average_time, key=lambda x: max_time[x])],
    [max_time[vendor] for vendor in sorted(average_time, key=lambda x: max_time[x])],
    color='red',
    alpha=0.5,
    label='Maximum Time'
)
plt.barh(
    [vendor.replace('_', ' ').title() for vendor in sorted(average_time, key=lambda x: max_time[x])],
    [average_time[vendor] for vendor in sorted(average_time, key=lambda x: max_time[x])],
    color='green',
    alpha=0.8,
    label='Average Time'
)
plt.barh(
    [vendor.replace('_', ' ').title() for vendor in sorted(average_time, key=lambda x: max_time[x])],
    [min_time[vendor] for vendor in sorted(average_time, key=lambda x: max_time[x])],
    color='blue',
    alpha=0.5,
    label='Minimum Time'
)
plt.ylabel('Vendor')
plt.xlabel('Time (s)')
plt.title('Time until device is available to user for each platform in FakeNOS')
plt.legend()
plt.xticks(np.arange(0, 2, 0.1))  # Set y-axis ticks to be in increments of 0.1
# Add horizontal lines for each vertical line
for i in np.arange(0, 2, 0.1):
    plt.axvline(x=i, color='gray', linestyle='dotted', alpha=0.2)
plt.tight_layout()
plt.subplots_adjust(left=0.2)
plt.savefig('results_time.png', dpi=300)
plt.savefig('results_time.svg', dpi=300)
plt.show()


# plot the time until the device is available to the user in vyatta_vyos
plt.ylabel('Time (s)')
plt.xlabel('Round Number')
plt.title('Time until device is available to user in Huawei Smartax')
plt.plot(huawei_smartax[' Time taken'])
plt.show()


# Calculate the average time for each vendor

# Calculate the standard deviation for each vendor
# std_dev = df.std()

# # Plot the bar graph with error bars
# # plt.barh(average_time.sort_values(ascending=True).index, average_time.sort_values(ascending=True).values, xerr=std_dev.sort_values(ascending=True).values, capsize=5)
# plt.ylabel('Vendor')
# plt.xlabel('Average Time')
# plt.title('Average Time to access for each platform in Netmiko')
# plt.xticks(range(0, 12, 1))  # Set y-axis ticks to be in increments of 5
# # Add horizontal lines for each vertical line
# for i in range(0,12,1):
#     plt.axvline(x=i, color='gray', linestyle='dotted', alpha=0.2)
# plt.tight_layout()
# plt.subplots_adjust(left=0.2)
# plt.savefig('results.png', dpi=300)
# plt.savefig('results.svg', dpi=300)
# plt.show()
