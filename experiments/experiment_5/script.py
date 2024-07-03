"""
Gathers the running services in an OLT
and print out the results in a CSV file.
"""
import csv
import asyncio
import socket
import time
import timeit
import logging
from concurrent.futures import wait, ALL_COMPLETED, ThreadPoolExecutor
from fakenos import FakeNOS
from fakenos.core.nos import available_platforms

from netmiko import ConnectHandler
from netmiko.ssh_dispatcher import CLASS_MAPPER_BASE

from scrapli import AsyncScrapli

import paramiko

from ssh2.session import Session


logger = logging.getLogger("fakenos.plugins.servers.ssh_server_paramiko")
logger.setLevel(logging.DEBUG)

# import asyncssh

N_ROUNDS = 2
N_HOSTS = [1, 2, 4, 8, 16, 32, 64, 128]

inventory_base = {
    "hosts": {
        "R": {
            "username": "user",
            "password": "user",
        }
    }
}


### NETMIKO ###
def netmiko_handler(credential):
    connect_start = timeit.default_timer()
    with ConnectHandler(**credential) as conn:
        time_to_connect = timeit.default_timer() - connect_start
        command_start = timeit.default_timer()
        conn.send_command("enable", auto_find_prompt=False)
        time_to_send_command = timeit.default_timer() - command_start
        disconnect_start = timeit.default_timer()
    time_to_disconnect = timeit.default_timer() - disconnect_start
    return time_to_connect, time_to_send_command, time_to_disconnect


netmiko_platforms = list(set(available_platforms) & set(CLASS_MAPPER_BASE.keys()))
netmiko_platforms = [platform for platform in netmiko_platforms if "yamaha" not in platform]

for hosts in N_HOSTS:
    break
    print(f'Number of hosts: {hosts}')
    for round in range(N_ROUNDS):
        print(f'Round {round + 1}/{N_ROUNDS}')
        for platform in netmiko_platforms:
            print(f'Platform: {platform}')
            inventory = {
                "hosts": {
                    **inventory_base["hosts"],
                    "R": {
                        **inventory_base["hosts"]["R"],
                        "platform": platform,
                        "port": [6000, 6000+hosts-1] if hosts > 1 else 6000
                    }
                }
            }
            if hosts > 1:
                inventory["hosts"]["R"]["replicas"] = hosts
            credentials = [{
                "host": "localhost",
                "username": "user",
                "password": "user",
                "device_type": platform,
                "port": 6000+i
            } for i in range(hosts)]
            with FakeNOS(inventory):
                with ThreadPoolExecutor(max_workers=hosts) as executor:
                    futures = []
                    results = []
                    for host in range(hosts):
                        credential = credentials[host]
                        futures.append(executor.submit(netmiko_handler, credential))
                    wait(futures, return_when=ALL_COMPLETED)
                    for future in futures:
                        result = future.result()
                        results.append(result)
                    min_connection = min([result[0] for result in results])
                    max_connection = max([result[0] for result in results])
                    avg_connection = sum([result[0] for result in results]) / hosts
                    min_command = min([result[1] for result in results])
                    max_command = max([result[1] for result in results])
                    avg_command = sum([result[1] for result in results]) / hosts
                    min_disconnection = min([result[2] for result in results])
                    max_disconnection = max([result[2] for result in results])
                    avg_disconnection = sum([result[2] for result in results]) / hosts
                    with open(f"netmiko/{platform}_{hosts}.csv", "a+", encoding="utf-8") as file:
                        writer = csv.writer(file)
                        writer.writerow([min_connection, max_connection, avg_connection, 
                                         min_command, max_command, avg_command, 
                                         min_disconnection, max_disconnection, avg_disconnection])
        
### SCRAPLI ###
async def scrapli_handler(credential):
    connect_start = timeit.default_timer()
    print("CONNECTANDO")
    async with AsyncScrapli(**credential) as conn:
        print("CONECTADO")
        time_to_connect = timeit.default_timer() - connect_start
        command_start = timeit.default_timer()
        await conn.send_command("enable")
        time_to_send_command = timeit.default_timer() - command_start
        disconnect_start = timeit.default_timer()
    time_to_disconnect = timeit.default_timer() - disconnect_start
    return time_to_connect, time_to_send_command, time_to_disconnect

async def run_scrapli_gather(credentials):
    results = await asyncio.gather(*[scrapli_handler(credential) for credential in credentials])
    return results

scrapli_to_netmiko = {
    "cisco_nxos": "cisco_nxos",
    "cisco_iosxr": "cisco_xr",
    "juniper_junos": "juniper_junos",
    "arista_eos": "arista_eos",
}

for hosts in N_HOSTS:
    break
    print(f'Number of hosts: {hosts}')
    for round in range(N_ROUNDS):
        print(f'Round {round + 1}/{N_ROUNDS}')
        for platform, netmiko_platform in scrapli_to_netmiko.items():
            print(f'Platform: {platform}')
            inventory = {
                "hosts": {
                    **inventory_base["hosts"],
                    "R": {
                        **inventory_base["hosts"]["R"],
                        "platform": netmiko_platform,
                        "port": [6000, 6000+hosts-1] if hosts > 1 else 6000
                    }
                }
            }
            if hosts > 1:
                inventory["hosts"]["R"]["replicas"] = hosts
            credentials = [{
                "host": "localhost",
                "auth_username": "user",
                "auth_password": "user",
                "platform": platform,
                "auth_strict_key": False,
                "transport": "asyncssh",
                "port": 6000+i
            } for i in range(hosts)]
            with FakeNOS(inventory):
                results = asyncio.run(run_scrapli_gather(credentials))
                min_connection = min([result[0] for result in results])
                max_connection = max([result[0] for result in results])
                avg_connection = sum([result[0] for result in results]) / hosts
                min_command = min([result[1] for result in results])
                max_command = max([result[1] for result in results])
                avg_command = sum([result[1] for result in results]) / hosts
                min_disconnection = min([result[2] for result in results])
                max_disconnection = max([result[2] for result in results])
                avg_disconnection = sum([result[2] for result in results]) / hosts
                with open(f"scrapli/{netmiko_platform}_{hosts}.csv", "a+", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerow([min_connection, max_connection, avg_connection, 
                                     min_command, max_command, avg_command,
                                    min_disconnection, max_disconnection, avg_disconnection])

### PARAMIKO ###
def paramiko_handler(credential):
    hostname = credential['host']
    username = credential['username']
    password = credential['password']
    port = credential.get('port', 22)

    connect_start = timeit.default_timer()

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port=port, username=username, password=password)
    
    time_to_connect = timeit.default_timer() - connect_start

    command_start = timeit.default_timer()

    # Create an interactive shell session
    shell = client.invoke_shell()
    shell.send('enable\n')
    while not shell.recv_ready():
        time.sleep(0.01)
    
    time_to_send_command = timeit.default_timer() - command_start

    disconnect_start = timeit.default_timer()

    shell.close()
    client.close()
    
    time_to_disconnect = timeit.default_timer() - disconnect_start

    return time_to_connect, time_to_send_command, time_to_disconnect

for hosts in N_HOSTS:
    break
    print(f'Number of hosts: {hosts}')
    for round in range(N_ROUNDS):
        print(f'Round {round + 1}/{N_ROUNDS}')
        for platform in netmiko_platforms:
            print(f'Platform: {platform}')
            inventory = {
                "hosts": {
                    **inventory_base["hosts"],
                    "R": {
                        **inventory_base["hosts"]["R"],
                        "platform": platform,
                        "port": [6000, 6000+hosts-1] if hosts > 1 else 6000
                    }
                }
            }
            if hosts > 1:
                inventory["hosts"]["R"]["replicas"] = hosts
            credentials = [{
                "host": "localhost",
                "username": "user",
                "password": "user",
                "device_type": platform,
                "port": 6000+i
            } for i in range(hosts)]
            with FakeNOS(inventory):
                with ThreadPoolExecutor(max_workers=hosts) as executor:
                    futures = []
                    results = []
                    for host in range(hosts):
                        credential = credentials[host]
                        futures.append(executor.submit(paramiko_handler, credential))
                    wait(futures, return_when=ALL_COMPLETED)
                    for future in futures:
                        result = future.result()
                        results.append(result)
                    min_connection = min([result[0] for result in results])
                    max_connection = max([result[0] for result in results])
                    avg_connection = sum([result[0] for result in results]) / hosts
                    min_command = min([result[1] for result in results])
                    max_command = max([result[1] for result in results])
                    avg_command = sum([result[1] for result in results]) / hosts
                    min_disconnection = min([result[2] for result in results])
                    max_disconnection = max([result[2] for result in results])
                    avg_disconnection = sum([result[2] for result in results]) / hosts
                    with open(f"paramiko/{platform}_{hosts}.csv", "a+", encoding="utf-8") as file:
                        writer = csv.writer(file)
                        writer.writerow([min_connection, max_connection, avg_connection, 
                                         min_command, max_command, avg_command, 
                                         min_disconnection, max_disconnection, avg_disconnection])
        
### ASYNCSSH ###

### PYTHON-SSH2 ###
def python_ssh2_handler(credential):
    hostname = credential['host']
    username = credential['username']
    password = credential['password']
    port = credential.get('port', 22)

    connect_start = timeit.default_timer()
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((hostname, port))
    session = Session()
    session.handshake(sock)
    session.userauth_password(username, password)
    channel = session.open_session()
    time_to_connect = timeit.default_timer() - connect_start

    command_start = timeit.default_timer()
    channel.execute("h")
    channel.wait_eof()

    time_to_send_command = timeit.default_timer() - command_start

    disconnect_start = timeit.default_timer()

    channel.close()
    channel.wait_closed()

    time_to_disconnect = timeit.default_timer() - disconnect_start

    return time_to_connect, time_to_send_command, time_to_disconnect

for hosts in N_HOSTS:
    print(f'Number of hosts: {hosts}')
    for round in range(N_ROUNDS):
        print(f'Round {round + 1}/{N_ROUNDS}')
        for platform in netmiko_platforms:
            print(f'Platform: {platform}')
            inventory = {
                "hosts": {
                    **inventory_base["hosts"],
                    "R": {
                        **inventory_base["hosts"]["R"],
                        "platform": platform,
                        "port": [6000, 6000+hosts-1] if hosts > 1 else 6000
                    }
                }
            }
            if hosts > 1:
                inventory["hosts"]["R"]["replicas"] = hosts
            credentials = [{
                "host": "localhost",
                "username": "user",
                "password": "user",
                "device_type": platform,
                "port": 6000+i
            } for i in range(hosts)]
            with FakeNOS(inventory):
                with ThreadPoolExecutor(max_workers=hosts) as executor:
                    futures = []
                    results = []
                    for host in range(hosts):
                        credential = credentials[host]
                        futures.append(executor.submit(python_ssh2_handler, credential))
                    wait(futures, return_when=ALL_COMPLETED)
                    for future in futures:
                        result = future.result()
                        results.append(result)
                    min_connection = min([result[0] for result in results])
                    max_connection = max([result[0] for result in results])
                    avg_connection = sum([result[0] for result in results]) / hosts
                    min_command = min([result[1] for result in results])
                    max_command = max([result[1] for result in results])
                    avg_command = sum([result[1] for result in results]) / hosts
                    min_disconnection = min([result[2] for result in results])
                    max_disconnection = max([result[2] for result in results])
                    avg_disconnection = sum([result[2] for result in results]) / hosts
                    with open(f"paramiko/{platform}_{hosts}.csv", "a+", encoding="utf-8") as file:
                        writer = csv.writer(file)
                        writer.writerow([min_connection, max_connection, avg_connection, 
                                         min_command, max_command, avg_command, 
                                         min_disconnection, max_disconnection, avg_disconnection])
