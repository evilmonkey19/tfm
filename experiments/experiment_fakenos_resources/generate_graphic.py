import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

platforms = [
    'alcatel_aos', 'alcatel_sros', 'allied_telesis_awplus', 'arista_eos', 'aruba_os',
    'avaya_ers', 'avaya_vsp', 'broadcom_icos', 'brocade_netiron', 'checkpoint_gaia',
    'cisco_asa', 'cisco_ftd', 'cisco_nxos', 'cisco_s300', 'cisco_xr', 'dell_force10',
    'dlink_ds', 'eltex', 'ericsson_ipos', 'extreme_exos', 'hp_comware', 'hp_procurve',
    'huawei_smartax', 'huawei_vrp', 'ipinfusion_ocnos', 'juniper_junos', 'linux',
    'ubiquiti_edgerouter', 'ubiquiti_edgeswitch', 'vyatta_vyos', 'zyxel_os'
]

n_hosts = [1, 2, 4, 8, 16, 32, 64, 128]

results = {
    "cpu_usage": [],
    "memory_usage": [],
    "time": []
}

for platform in platforms:
    for n_host in n_hosts:
        df = pd.read_csv(f"fakenos/{platform}_{n_host}.csv")
        results["cpu_usage"].append((platform, n_host, df['CPU time'].mean(), df['CPU time'].std()))
        results["memory_usage"].append((platform, n_host, df[' RAM usage'].mean(), df[' RAM usage'].std()))
        results["time"].append((platform, n_host, df[' Time taken'].mean(), df[' Time taken'].std()))

# for each platform do a bar graph with the average cpu usage per host number and the standard deviation as error bar
for platform in platforms:
    df = pd.DataFrame(results["cpu_usage"], columns=["Platform", "Hosts", "CPU Usage", "Std Dev"])
    df = df[df["Platform"] == platform]
    plt.errorbar([str(n) for n in n_hosts], df["CPU Usage"], yerr=df["Std Dev"], capsize=5)
    plt.xlabel("Number of Hosts")
    plt.ylabel("Average CPU Usage (%)")
    plt.title(f"Average CPU Usage for {platform} in FakeNOS")
    plt.xticks([str(n) for n in n_hosts])
    plt.savefig(f"graphs/cpu_usage_{platform}.png", dpi=300)
    plt.close()

    df = pd.DataFrame(results["memory_usage"], columns=["Platform", "Hosts", "Memory Usage", "Std Dev"])
    df = df[df["Platform"] == platform]
    plt.errorbar([str(n) for n in n_hosts], df["Memory Usage"]/1024, yerr=df["Std Dev"]/1024, capsize=5)
    plt.xlabel("Number of Hosts")
    plt.ylabel("Average Memory Usage (kb)")
    plt.title(f"Average Memory Usage for {platform} in FakeNOS")
    plt.xticks([str(n) for n in n_hosts])
    plt.savefig(f"graphs/memory_usage_{platform}.png", dpi=300)
    plt.close()

    df = pd.DataFrame(results["time"], columns=["Platform", "Hosts", "Time", "Std Dev"])
    df = df[df["Platform"] == platform]
    plt.errorbar([str(n) for n in n_hosts], df["Time"], yerr=df["Std Dev"], capsize=5)
    plt.xlabel("Number of Hosts")
    plt.ylabel("Average Time Taken (s)")
    plt.title(f"Average Time Taken for {platform} in FakeNOS")
    plt.xticks([str(n) for n in n_hosts])
    plt.savefig(f"graphs/time_{platform}.png", dpi=300)
    plt.close()


platforms_to_plot = ["huawei_smartax", "cisco_nxos", "juniper_junos", "linux", "arista_eos"]
### CPU ###
for platform in platforms_to_plot:
    df = pd.DataFrame(results["cpu_usage"], columns=["Platform", "Hosts", "CPU Usage", "Std Dev"])
    df = df[df["Platform"] == platform]
    plt.plot([str(n) for n in n_hosts], df["CPU Usage"], label=platform, marker='o')
plt.xlabel("Number of Hosts")
plt.ylabel("Average CPU Usage (%)")
plt.title("Average CPU Usage for FakeNOS")
plt.legend(loc=2)
plt.savefig("graphs/cpu_5.png", dpi=300)
plt.close()

for platform in platforms:
    df = pd.DataFrame(results["cpu_usage"], columns=["Platform", "Hosts", "CPU Usage", "Std Dev"])
    df = df[df["Platform"] == platform]
    plt.plot([str(n) for n in n_hosts], df["CPU Usage"], label=platform)
plt.xlabel("Number of Hosts")
plt.ylabel("Average CPU Usage (%)")
plt.title("Average CPU Usage for FakeNOS")
plt.legend(loc=2, fontsize=5)
plt.savefig("graphs/cpu_all.png", dpi=300)
plt.close()

### Memory ###
for platform in platforms_to_plot:
    df = pd.DataFrame(results["memory_usage"], columns=["Platform", "Hosts", "Memory Usage", "Std Dev"])
    df = df[df["Platform"] == platform]
    plt.plot([str(n) for n in n_hosts], df["Memory Usage"]/1024, label=platform, marker='o')
plt.xlabel("Number of Hosts")
plt.ylabel("Average Memory Usage (KB)")
plt.title("Average Memory Usage for FakeNOS")
plt.legend(loc=2)
plt.savefig("graphs/memory_5.png", dpi=300)
plt.close()

for platform in platforms:
    df = pd.DataFrame(results["memory_usage"], columns=["Platform", "Hosts", "Memory Usage", "Std Dev"])
    df = df[df["Platform"] == platform]
    plt.plot([str(n) for n in n_hosts], df["Memory Usage"]/1024, label=platform)
plt.xlabel("Number of Hosts")
plt.ylabel("Average Memory Usage (KB)")
plt.title("Average Memory Usage for FakeNOS")
plt.legend(loc=2, fontsize=5)
plt.savefig("graphs/memory_all.png", dpi=300)
plt.close()

### Time taken ###
for platform in platforms_to_plot:
    df = pd.DataFrame(results["time"], columns=["Platform", "Hosts", "Time", "Std Dev"])
    df = df[df["Platform"] == platform]
    plt.plot([str(n) for n in n_hosts], df["Time"], label=platform, marker='o')
plt.xlabel("Number of Hosts")
plt.ylabel("Average Time Taken (s)")
plt.title("Average Time Taken for FakeNOS")
plt.legend(loc=2)
plt.savefig("graphs/time_5.png", dpi=300)
plt.close()

for platform in platforms:
    df = pd.DataFrame(results["time"], columns=["Platform", "Hosts", "Time", "Std Dev"])
    df = df[df["Platform"] == platform]
    plt.plot([str(n) for n in n_hosts], df["Time"], label=platform)
plt.xlabel("Number of Hosts")
plt.ylabel("Average Time Taken (s)")
plt.title("Average Time Taken for FakeNOS")
plt.legend(loc=2, fontsize=5)
plt.savefig("graphs/time_all.png", dpi=300)
plt.close()