import pandas as pd
import numpy as np
import os

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

ssh_libraries = ["netmiko", "scrapli", "paramiko", "asyncssh", "ssh2_python"]

results = {}

for platform in platforms:
    for n_host in n_hosts:
        for tool in ssh_libraries:
            if not os.path.isfile(f"{tool}/{platform}_{n_host}.csv"):
                continue
            print(f"Reading {tool}/{platform}_{n_host}.csv")
            results[f'{tool}_{platform}_{n_host}'] = pd.read_csv(f"{tool}/{platform}_{n_host}.csv")

### NETMIKO VS SCRAPLI ###

plot_platforms = ['cisco_nxos', 'juniper_junos', 'arista_eos', 'cisco_xr']
BAR_WIDTH = 0.3
x = np.arange(len(n_hosts))
_ssh_libraries = ["netmiko", "scrapli"]
_n_hosts = [1, 2, 4, 8, 16, 32, 64, 128]

### TOTAL TIME ###
fig, ax = plt.subplots(4, figsize=(10, 8))
for i, plot_platform in enumerate(plot_platforms):
    for index, library in enumerate(_ssh_libraries):
        n_hosts_library = [n for n in _n_hosts if f'{library}_{plot_platform}_{n}' in results]
        _x = np.arange(len(n_hosts_library))
        _avg_connection = [results[f'{library}_{plot_platform}_{n}']["avg_connection"].mean() for n in n_hosts_library]
        _avg_disconnect = [results[f'{library}_{plot_platform}_{n}']["avg_disconnect"].mean() for n in n_hosts_library]
        _avg_send_command = [results[f'{library}_{plot_platform}_{n}']["avg_send_command"].mean() for n in n_hosts_library]
        _result = np.array(_avg_connection) + np.array(_avg_disconnect) + np.array(_avg_send_command)
        ax[i].bar(_x+BAR_WIDTH*(index-1), _result, BAR_WIDTH, capsize=5)

    ax[i].set_xticks(_x-BAR_WIDTH/2)
    ax[i].set_yticks(np.arange(0, 30, 5))
    ax[i].set_xticklabels([str(n) for n in _n_hosts])
    ax[i].set_title(plot_platform)
    ax[i].tick_params(axis='x', pad=10)
    ax[i].legend(_ssh_libraries)
    ax[i].set_axisbelow(True)
    ax[i].grid(color = 'gray', linestyle = '--', linewidth = 0.5)

for ax in fig.get_axes():
    ax.label_outer()
fig.suptitle("Total Time for Netmiko vs Scrapli")
fig.supylabel("Average Total Time (s)")
fig.supxlabel("Number of Hosts")
plt.tight_layout()
plt.savefig(f"graphs/total_netmiko_vs_scrapli.png", dpi=300)
plt.close()


### CONNECTION TIME ###
fig, ax = plt.subplots(4, figsize=(10, 8))
for i, plot_platform in enumerate(plot_platforms):
    for index, library in enumerate(_ssh_libraries):
        n_hosts_library = [n for n in _n_hosts if f'{library}_{plot_platform}_{n}' in results]
        _x = np.arange(len(n_hosts_library))
        _avg_connection = [results[f'{library}_{plot_platform}_{n}']["avg_connection"].mean() for n in n_hosts_library]
        ax[i].bar(_x+BAR_WIDTH*(index-1), _avg_connection, BAR_WIDTH, capsize=5)
    
    ax[i].set_xticks(_x-BAR_WIDTH/2)
    ax[i].set_yticks(np.arange(0, 30, 5))
    ax[i].set_xticklabels([str(n) for n in _n_hosts])
    ax[i].set_title(plot_platform)
    ax[i].tick_params(axis='x', pad=10)
    ax[i].legend(_ssh_libraries)
    ax[i].set_axisbelow(True)
    ax[i].grid(color = 'gray', linestyle = '--', linewidth = 0.5)

for ax in fig.get_axes():
    ax.label_outer()
fig.suptitle("Connection Time for Netmiko vs Scrapli")
fig.supylabel("Average Connection Time (s)")
fig.supxlabel("Number of Hosts")
plt.tight_layout()
plt.savefig(f"graphs/connection_netmiko_vs_scrapli.png", dpi=300)
plt.close()

### DISCONNECT TIME ###
fig, ax = plt.subplots(4, figsize=(10, 8))
for i, plot_platform in enumerate(plot_platforms):
    for index, library in enumerate(_ssh_libraries):
        n_hosts_library = [n for n in _n_hosts if f'{library}_{plot_platform}_{n}' in results]
        _x = np.arange(len(n_hosts_library))
        _avg_disconnect = [results[f'{library}_{plot_platform}_{n}']["avg_disconnect"].mean() for n in n_hosts_library]
        ax[i].bar(_x+BAR_WIDTH*(index-1), _avg_disconnect, BAR_WIDTH, capsize=5)

    ax[i].set_xticks(_x-BAR_WIDTH/2)
    ax[i].set_yticks(np.arange(0, 15, 5))
    ax[i].set_xticklabels([str(n) for n in _n_hosts])
    ax[i].set_title(plot_platform)
    ax[i].tick_params(axis='x', pad=10)
    ax[i].legend(_ssh_libraries)
    ax[i].set_axisbelow(True)
    ax[i].grid(color = 'gray', linestyle = '--', linewidth = 0.5)

for ax in fig.get_axes():
    ax.label_outer()
fig.suptitle("Disconnect Time for Netmiko vs Scrapli")
fig.supylabel("Average Disconnect Time (s)")
fig.supxlabel("Number of Hosts")
plt.tight_layout()
plt.savefig(f"graphs/disconnect_netmiko_vs_scrapli.png", dpi=300)
plt.close()

### SEND COMMAND TIME ###
fig, ax = plt.subplots(4, figsize=(10, 8))
for i, plot_platform in enumerate(plot_platforms):
    for index, library in enumerate(_ssh_libraries):
        n_hosts_library = [n for n in _n_hosts if f'{library}_{plot_platform}_{n}' in results]
        _x = np.arange(len(n_hosts_library))
        _avg_send_command = [results[f'{library}_{plot_platform}_{n}']["avg_send_command"].mean() for n in n_hosts_library]
        ax[i].bar(_x+BAR_WIDTH*(index-1), _avg_send_command, BAR_WIDTH, capsize=5)

    ax[i].set_xticks(_x-BAR_WIDTH/2)
    ax[i].set_yticks(np.arange(0, 5, 1))
    ax[i].set_xticklabels([str(n) for n in _n_hosts])
    ax[i].set_title(plot_platform)
    ax[i].tick_params(axis='x', pad=10)
    ax[i].legend(_ssh_libraries)
    ax[i].set_axisbelow(True)
    ax[i].grid(color = 'gray', linestyle = '--', linewidth = 0.5)

for ax in fig.get_axes():
    ax.label_outer()
fig.suptitle("Send Command Time for Netmiko vs Scrapli")
fig.supylabel("Average Send Command Time (s)")
fig.supxlabel("Number of Hosts")
plt.tight_layout()
plt.savefig(f"graphs/send_command_netmiko_vs_scrapli.png", dpi=300)
plt.close()

### Paramiko vs. AsyncSSH ###
plot_platforms = ['cisco_nxos', 'juniper_junos', 'arista_eos', 'cisco_xr']
BAR_WIDTH = 0.3
x = np.arange(len(n_hosts))
_ssh_libraries = ["paramiko", "asyncssh"]
_n_hosts = [1, 2, 4, 8, 16, 32, 64, 128]

### TOTAL TIME ###
fig, ax = plt.subplots(4, figsize=(10, 8))
for i, plot_platform in enumerate(plot_platforms):
    for index, library in enumerate(_ssh_libraries):
        n_hosts_library = [n for n in _n_hosts if f'{library}_{plot_platform}_{n}' in results]
        _x = np.arange(len(n_hosts_library))
        _avg_connection = [results[f'{library}_{plot_platform}_{n}']["avg_connection"].mean() for n in n_hosts_library]
        _avg_disconnect = [results[f'{library}_{plot_platform}_{n}']["avg_disconnect"].mean() for n in n_hosts_library]
        _avg_send_command = [results[f'{library}_{plot_platform}_{n}']["avg_send_command"].mean() for n in n_hosts_library]
        _result = np.array(_avg_connection) + np.array(_avg_disconnect) + np.array(_avg_send_command)
        ax[i].bar(_x+BAR_WIDTH*(index-1), _result, BAR_WIDTH, capsize=5)
    
    ax[i].set_xticks(_x-BAR_WIDTH/2)
    ax[i].set_yticks(np.arange(0, 10, 2))
    ax[i].set_xticklabels([str(n) for n in _n_hosts])
    ax[i].set_title(plot_platform)
    ax[i].tick_params(axis='x', pad=10)
    ax[i].legend(_ssh_libraries)
    ax[i].set_axisbelow(True)
    ax[i].grid(color = 'gray', linestyle = '--', linewidth = 0.5)

for ax in fig.get_axes():
    ax.label_outer()
fig.suptitle("Total Time for Paramiko vs AsyncSSH")
fig.supylabel("Average Total Time (s)")
fig.supxlabel("Number of Hosts")
plt.tight_layout()
plt.savefig(f"graphs/total_paramiko_vs_asyncssh.png", dpi=300)
plt.close()

### CONNECTION TIME ###
fig, ax = plt.subplots(4, figsize=(10, 8))
for i, plot_platform in enumerate(plot_platforms):
    for index, library in enumerate(_ssh_libraries):
        n_hosts_library = [n for n in _n_hosts if f'{library}_{plot_platform}_{n}' in results]
        _x = np.arange(len(n_hosts_library))
        _avg_connection = [results[f'{library}_{plot_platform}_{n}']["avg_connection"].mean() for n in n_hosts_library]
        ax[i].bar(_x+BAR_WIDTH*(index-1), _avg_connection, BAR_WIDTH, capsize=5)
    
    ax[i].set_xticks(_x-BAR_WIDTH/2)
    ax[i].set_yticks(np.arange(0, 2, 0.5))
    ax[i].set_xticklabels([str(n) for n in _n_hosts])
    ax[i].set_title(plot_platform)
    ax[i].tick_params(axis='x', pad=10)
    ax[i].legend(_ssh_libraries)
    ax[i].set_axisbelow(True)
    ax[i].grid(color = 'gray', linestyle = '--', linewidth = 0.5)

for ax in fig.get_axes():
    ax.label_outer()
fig.suptitle("Connection Time for Paramiko vs AsyncSSH")
fig.supylabel("Average Connection Time (s)")
fig.supxlabel("Number of Hosts")
plt.tight_layout()
plt.savefig(f"graphs/connection_paramiko_vs_asyncssh.png", dpi=300)
plt.close()

### DISCONNECT TIME ###
fig, ax = plt.subplots(4, figsize=(10, 8))
for i, plot_platform in enumerate(plot_platforms):
    for index, library in enumerate(_ssh_libraries):
        n_hosts_library = [n for n in _n_hosts if f'{library}_{plot_platform}_{n}' in results]
        _x = np.arange(len(n_hosts_library))
        _avg_disconnect = [results[f'{library}_{plot_platform}_{n}']["avg_disconnect"].mean() for n in n_hosts_library]
        ax[i].bar(_x+BAR_WIDTH*(index-1), _avg_disconnect, BAR_WIDTH, capsize=5)

    ax[i].set_xticks(_x-BAR_WIDTH/2)
    ax[i].set_yticks(np.arange(0, 1, 0.2))
    ax[i].set_xticklabels([str(n) for n in _n_hosts])
    ax[i].set_title(plot_platform)
    ax[i].tick_params(axis='x', pad=10)
    ax[i].legend(_ssh_libraries)
    ax[i].set_axisbelow(True)
    ax[i].grid(color = 'gray', linestyle = '--', linewidth = 0.5)

for ax in fig.get_axes():
    ax.label_outer()
fig.suptitle("Disconnect Time for Paramiko vs AsyncSSH")
fig.supylabel("Average Disconnect Time (s)")
fig.supxlabel("Number of Hosts")
plt.tight_layout()
plt.savefig(f"graphs/disconnect_paramiko_vs_asyncssh.png", dpi=300)
plt.close()

### SEND COMMAND TIME ###
fig, ax = plt.subplots(4, figsize=(10, 8))
for i, plot_platform in enumerate(plot_platforms):
    for index, library in enumerate(_ssh_libraries):
        n_hosts_library = [n for n in _n_hosts if f'{library}_{plot_platform}_{n}' in results]
        _x = np.arange(len(n_hosts_library))
        _avg_send_command = [results[f'{library}_{plot_platform}_{n}']["avg_send_command"].mean() for n in n_hosts_library]
        ax[i].bar(_x+BAR_WIDTH*(index-1), _avg_send_command, BAR_WIDTH, capsize=5)

    ax[i].set_xticks(_x-BAR_WIDTH/2)
    ax[i].set_yticks(np.arange(0, 6, 1))
    ax[i].set_xticklabels([str(n) for n in _n_hosts])
    ax[i].set_title(plot_platform)
    ax[i].tick_params(axis='x', pad=10)
    ax[i].legend(_ssh_libraries)
    ax[i].set_axisbelow(True)
    ax[i].grid(color = 'gray', linestyle = '--', linewidth = 0.5)

for ax in fig.get_axes():
    ax.label_outer()
fig.suptitle("Send Command Time for Paramiko vs AsyncSSH")
fig.supylabel("Average Send Command Time (s)")
fig.supxlabel("Number of Hosts")
plt.tight_layout()
plt.savefig(f"graphs/send_command_paramiko_vs_asyncssh.png", dpi=300)
plt.close()


_platform = 'cisco_xr'
BAR_WIDTH = 0.15

for index, library in enumerate(ssh_libraries):
    n_hosts_library = [n for n in n_hosts if f'{library}_{_platform}_{n}' in results]
    if not n_hosts_library:
        continue
    _x = np.arange(len(n_hosts_library))
    _avg_connection = [results[f'{library}_{_platform}_{n}']["avg_connection"].mean() for n in n_hosts_library]
    _avg_disconnect = [results[f'{library}_{_platform}_{n}']["avg_disconnect"].mean() for n in n_hosts_library]
    _avg_send_command = [results[f'{library}_{_platform}_{n}']["avg_send_command"].mean() for n in n_hosts_library]
    _total_time = np.array(_avg_connection) + np.array(_avg_disconnect) + np.array(_avg_send_command)
    
    plt.bar(_x-BAR_WIDTH*index, _total_time, BAR_WIDTH, label="Connection Time")

plt.xlabel("Number of Hosts")
plt.ylabel("Average Total Time (s)")
plt.title(f"Total Time for {_platform} in FakeNOS using all libraries.")
plt.xticks(np.arange(len(n_hosts))-BAR_WIDTH*2, [str(n) for n in n_hosts])
plt.legend(ssh_libraries)
plt.grid(color = 'gray', linestyle = '--', linewidth = 0.5)
plt.savefig(f"graphs/total_time_all_libraries.png", dpi=300)
plt.close()


### NETMIKO ALL PLATFORMS ###
avg_connect_netmiko_times = {platform: results[f"netmiko_{platform}_1"]["avg_connection"].mean() for platform in platforms if f"netmiko_{platform}_1" in results}
avg_send_command_netmiko_times = {platform: results[f"netmiko_{platform}_1"]["avg_send_command"].mean() for platform in platforms if f"netmiko_{platform}_1" in results}
avg_disconnect_netmiko_times = {platform: results[f"netmiko_{platform}_1"]["avg_disconnect"].mean() for platform in platforms if f"netmiko_{platform}_1" in results}

netmiko_times = {platform: avg_connect_netmiko_times[platform] + avg_send_command_netmiko_times[platform] + avg_disconnect_netmiko_times[platform] for platform in platforms if platform in avg_connect_netmiko_times}
netmiko_times = {k: v for k, v in sorted(netmiko_times.items(), key=lambda item: item[1], reverse=True)}

plt.barh(list(netmiko_times.keys()), list(netmiko_times.values()), zorder=2)
plt.xlabel("Average Total Time (s)")
plt.ylabel("Platform")
plt.title("Average Total Time of connection using Netmiko")
plt.grid(color='gray', linestyle='--', linewidth=0.5, zorder=3)
plt.xticks(np.arange(0, 12, 1))
plt.yticks(list(netmiko_times.keys()), fontsize=6)
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig("graphs/total_time_netmiko_platforms.png", dpi=300)
plt.close()

### SCRAPLI ALL PLATFORMS ###
avg_connect_scrapli_times = {platform: results[f"scrapli_{platform}_1"]["avg_connection"].mean() for platform in platforms if f"scrapli_{platform}_1" in results}
avg_send_command_scrapli_times = {platform: results[f"scrapli_{platform}_1"]["avg_send_command"].mean() for platform in platforms if f"scrapli_{platform}_1" in results}
avg_disconnect_scrapli_times = {platform: results[f"scrapli_{platform}_1"]["avg_disconnect"].mean() for platform in platforms if f"scrapli_{platform}_1" in results}

scrapli_times = {platform: avg_connect_scrapli_times[platform] + avg_send_command_scrapli_times[platform] + avg_disconnect_scrapli_times[platform] for platform in platforms if platform in avg_connect_scrapli_times}
scrapli_times = {k: v for k, v in sorted(scrapli_times.items(), key=lambda item: item[1], reverse=True)}

plt.barh(list(scrapli_times.keys()), list(scrapli_times.values()), zorder=2)
plt.xlabel("Average Total Time (s)")
plt.ylabel("Platform")
plt.title("Average Total Time of connection using Scrapli")
plt.grid(color='gray', linestyle='--', linewidth=0.5, zorder=3)
plt.xticks(np.arange(0, 2, 0.2))
plt.yticks(list(scrapli_times.keys()))
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig("graphs/total_time_scrapli_platforms.png", dpi=300)
plt.close()


_avg_connection = [results[f'netmiko_{platform}_{n}']["avg_connection"].mean() for n in n_hosts_library]
_avg_connection_dev = [results[f'netmiko_{platform}_{n}']["avg_connection"].std() for n in n_hosts_library]
_avg_disconnect = [results[f'netmiko_{platform}_{n}']["avg_disconnect"].mean() for n in n_hosts_library]
_avg_disconnect_dev = [results[f'netmiko_{platform}_{n}']["avg_disconnect"].std() for n in n_hosts_library]
_avg_send_command = [results[f'netmiko_{platform}_{n}']["avg_send_command"].mean() for n in n_hosts_library]
_avg_send_command_dev = [results[f'netmiko_{platform}_{n}']["avg_send_command"].std() for n in n_hosts_library]

_total_time = np.array(_avg_connection) + np.array(_avg_disconnect) + np.array(_avg_send_command)
_total_time_dev = np.sqrt(np.array(_avg_connection_dev)**2 + np.array(_avg_disconnect_dev)**2 + np.array(_avg_send_command_dev)**2)

plt.errorbar([str(n) for n in n_hosts_library], _avg_connection, yerr=_avg_connection_dev, fmt='o', ecolor='red')
plt.xlabel("Number of Hosts")
plt.ylabel("Average Connection Time (s)")
plt.title(f"Average Connection Time for {platform} in FakeNOS using Netmiko")
plt.xticks([str(n) for n in n_hosts_library])
# plt.show()
plt.savefig(f"graphs/netmiko/connection_time_{platform}.png", dpi=300)
plt.close()

plt.errorbar([str(n) for n in n_hosts_library], _avg_disconnect, yerr=_avg_disconnect_dev, fmt='o', ecolor='red')
plt.xlabel("Number of Hosts")
plt.ylabel("Average Disconnect Time (s)")
plt.title(f"Average Disconnect Time for {platform} in FakeNOS using Netmiko")

for library in ssh_libraries:
    for platform in platforms:
        n_hosts_library = [n for n in n_hosts if f'{library}_{platform}_{n}' in results]
        if not n_hosts_library:
            continue
        _x = np.arange(len(n_hosts_library))
        _avg_connection = [results[f'{library}_{platform}_{n}']["avg_connection"].mean() for n in n_hosts_library]
        _avg_connection_dev = [results[f'{library}_{platform}_{n}']["avg_connection"].std() for n in n_hosts_library]
        _avg_disconnect = [results[f'{library}_{platform}_{n}']["avg_disconnect"].mean() for n in n_hosts_library]
        _avg_disconnect_dev = [results[f'{library}_{platform}_{n}']["avg_disconnect"].std() for n in n_hosts_library]
        _avg_send_command = [results[f'{library}_{platform}_{n}']["avg_send_command"].mean() for n in n_hosts_library]
        _avg_send_command_dev = [results[f'{library}_{platform}_{n}']["avg_send_command"].std() for n in n_hosts_library]

        _total_time = np.array(_avg_connection) + np.array(_avg_disconnect) + np.array(_avg_send_command)
        _total_time_dev = np.sqrt(np.array(_avg_connection_dev)**2 + np.array(_avg_disconnect_dev)**2 + np.array(_avg_send_command_dev)**2)

        plt.errorbar([str(n) for n in n_hosts_library], _avg_connection, yerr=_avg_connection_dev, fmt='o', ecolor='red')
        plt.xlabel("Number of Hosts")
        plt.ylabel("Average Connection Time (s)")
        plt.title(f"Average Connection Time for {platform} in FakeNOS using {library}")
        plt.xticks([str(n) for n in n_hosts_library])
        # plt.show()
        plt.savefig(f"graphs/{library}/connection_time_{platform}.png", dpi=300)
        plt.close()

        plt.errorbar([str(n) for n in n_hosts_library], _avg_disconnect, yerr=_avg_disconnect_dev, fmt='o', ecolor='red')
        plt.xlabel("Number of Hosts")
        plt.ylabel("Average Disconnect Time (s)")
        plt.title(f"Average Disconnect Time for {platform} in FakeNOS using {library}")
        plt.xticks([str(n) for n in n_hosts_library])
        # plt.show()
        plt.savefig(f"graphs/{library}/disconnect_time_{platform}.png", dpi=300)
        plt.close()

        plt.errorbar([str(n) for n in n_hosts_library], _avg_send_command, yerr=_avg_send_command_dev, fmt='o', ecolor='red')
        plt.xlabel("Number of Hosts")
        plt.ylabel("Average Send Command Time (s)")
        plt.title(f"Average Send Command Time for {platform} in FakeNOS using {library}")
        plt.xticks([str(n) for n in n_hosts_library])
        # plt.show()
        plt.savefig(f"graphs/{library}/send_command_time_{platform}.png", dpi=300)
        plt.close()

        plt.errorbar([str(n) for n in n_hosts_library], _total_time, yerr=_total_time_dev, fmt='o', ecolor='red')
        plt.xlabel("Number of Hosts")
        plt.ylabel("Average Total Time (s)")
        plt.title(f"Average Total Time for {platform} in FakeNOS using {library}")
        plt.xticks([str(n) for n in n_hosts_library])
        # plt.show()
        plt.savefig(f"graphs/{library}/total_time_{platform}.png", dpi=300)
        plt.close()

