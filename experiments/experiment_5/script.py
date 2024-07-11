"""
Gathers the running services in an OLT
and print out the results in a CSV file.
"""
import csv
import asyncio
import socket
import time
import timeit
from concurrent.futures import wait, ALL_COMPLETED, ThreadPoolExecutor
import multiprocessing
from fakenos import FakeNOS
from fakenos.core.nos import available_platforms

from netmiko import ConnectHandler
from netmiko.ssh_dispatcher import CLASS_MAPPER_BASE

from scrapli import AsyncScrapli

import paramiko

import asyncssh

from ssh2.session import Session


N_ROUNDS = 100
# N_HOSTS = [1, 2, 4, 8, 16, 32, 64, 128]
N_HOSTS = [64, 128]

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
netmiko_platforms = ["cisco_xr", "cisco_nxos", "juniper_junos", "arista_eos"]

def python_netmiko_test():
    for hosts in N_HOSTS:
        print(f'Netmiko: Number of hosts: {hosts}')
        for round in range(N_ROUNDS):
            print(f'Netmiko: Round {round + 1}/{N_ROUNDS}')
            for platform in netmiko_platforms:
                print(f'Netmiko: Platform: {platform}')
                inventory = {
                    "hosts": {
                        **inventory_base["hosts"],
                        "R": {
                            **inventory_base["hosts"]["R"],
                            "platform": platform,
                            "port": [5000, 5000+hosts-1] if hosts > 1 else 5000
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
                    "port": 5000+i
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
    async with AsyncScrapli(**credential) as conn:
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

def python_scrapli_test():
    for hosts in N_HOSTS:
        print(f'Scrapli: Number of hosts: {hosts}')
        for round in range(N_ROUNDS):
            print(f'Scrapli: Round {round + 1}/{N_ROUNDS}')
            for platform, netmiko_platform in scrapli_to_netmiko.items():
                print(f'Scrapli: Platform: {platform}')
                inventory = {
                    "hosts": {
                        **inventory_base["hosts"],
                        "R": {
                            **inventory_base["hosts"]["R"],
                            "platform": netmiko_platform,
                            "port": [7000, 7000+hosts-1] if hosts > 1 else 7000
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
                    "port": 7000+i
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

def python_paramiko_test():
    for hosts in N_HOSTS:
        print(f'Paramiko: Number of hosts: {hosts}')
        for round in range(N_ROUNDS):
            print(f'Paramiko: Round {round + 1}/{N_ROUNDS}')
            for platform in netmiko_platforms:
                print(f'Paramiko: Platform: {platform}')
                inventory = {
                    "hosts": {
                        **inventory_base["hosts"],
                        "R": {
                            **inventory_base["hosts"]["R"],
                            "platform": platform,
                            "port": [8000, 8000+hosts-1] if hosts > 1 else 8000
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
                    "port": 8000+i
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
async def get_prompt(proc):
    prompt: str = ''
    while True:
        data = await proc.stdout.read(1)
        prompt = prompt + data if data != '\n' else ''
        if data.endswith((">", "#", "$")):
            prompt.strip()
            break
    return prompt

async def send_command(proc, command: str, prompt: str):
    proc.stdin.write(command + "\r\n")
    await proc.stdin.drain()
    await _send_command(proc, command)
    output: str = await _get_output(proc, prompt)
    return output

async def _get_output(proc, prompt: str):
    output: str = ''
    while True:
        output += await proc.stdout.read(1)
        if output[-1] in ['#', '>', '$']:
            break
    return output

async def _send_command(proc, command: str):
    command_sent: str = ''
    while True:
        data = await proc.stdout.read(1)
        command_sent += data
        if command_sent == command + '\r\n':
            break

async def asyncssh_handler(credential):
    connect_start = timeit.default_timer()
    async with asyncssh.connect(**credential) as conn:
        time_to_connect = timeit.default_timer() - connect_start
        time_to_send_command = timeit.default_timer()
        async with conn.create_process(term_type='xterm') as proc:
            prompt = await get_prompt(proc)
            await send_command(proc, "enable", prompt)
        time_to_send_command = timeit.default_timer() - time_to_send_command
        disconnect_start = timeit.default_timer()
    time_to_disconnect = timeit.default_timer() - disconnect_start
    
    return time_to_connect, time_to_send_command, time_to_disconnect

async def run_asyncssh_gather(credentials):
    results = await asyncio.gather(*[asyncssh_handler(credential) for credential in credentials])
    return results

def python_asyncssh_test():
    for hosts in N_HOSTS:
        print(f'AsyncSSH: Number of hosts: {hosts}')
        for round in range(N_ROUNDS):
            print(f'AsyncSSH: Round {round + 1}/{N_ROUNDS}')
            for platform in netmiko_platforms:
                print(f'AsyncSSH: Platform: {platform}')
                inventory = {
                    "hosts": {
                        **inventory_base["hosts"],
                        "R": {
                            **inventory_base["hosts"]["R"],
                            "platform": platform,
                            "port": [9000, 9000+hosts-1] if hosts > 1 else 9000
                        }
                    }
                }
                if hosts > 1:
                    inventory["hosts"]["R"]["replicas"] = hosts
                credentials = [{
                    "host": "localhost",
                    "username": "user",
                    "password": "user",
                    "client_keys": None,
                    "known_hosts": None,
                    "port": 9000+i
                } for i in range(hosts)]
                with FakeNOS(inventory):
                    results = asyncio.run(run_asyncssh_gather(credentials))
                    min_connection = min([result[0] for result in results])
                    max_connection = max([result[0] for result in results])
                    avg_connection = sum([result[0] for result in results]) / hosts
                    min_command = min([result[1] for result in results])
                    max_command = max([result[1] for result in results])
                    avg_command = sum([result[1] for result in results]) / hosts
                    min_disconnection = min([result[2] for result in results])
                    max_disconnection = max([result[2] for result in results])
                    avg_disconnection = sum([result[2] for result in results]) / hosts
                    with open(f"asyncssh/{platform}_{hosts}.csv", "a+", encoding="utf-8") as file:
                        writer = csv.writer(file)
                        writer.writerow([min_connection, max_connection, avg_connection, 
                                        min_command, max_command, avg_command,
                                        min_disconnection, max_disconnection, avg_disconnection])

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
    prompt = ""
    while True:
        _, data = channel.read()
        if data.decode().endswith(('>', '#', '~$', "$")):
            data = data.decode().replace('>','').replace('#','').replace('$','').replace('~','')
            if '\n' in data:
                prompt = data.split('\n')[-1].strip()[:-1]
            else:
                prompt = data.strip()[:-1]
            break
    time_to_connect = timeit.default_timer() - connect_start
    command_start = timeit.default_timer()
    channel.write("enable" + "\n")
    while True:
        _, data = channel.read()
        if data.decode()[:-1].startswith(prompt):
            break
    time_to_send_command = timeit.default_timer() - command_start

    disconnect_start = timeit.default_timer()
    channel.close()
    sock.close()
    time_to_disconnect = timeit.default_timer() - disconnect_start

    return time_to_connect, time_to_send_command, time_to_disconnect

def python_ssh2_test():
    for hosts in N_HOSTS:
        print(f'Python-SSH2: Number of hosts: {hosts}')
        for round in range(N_ROUNDS):
            print(f'Python-SSH2: Round {round + 1}/{N_ROUNDS}')
            for platform in netmiko_platforms:
                print(f'Python-SSH2: Platform: {platform}')
                inventory = {
                    "hosts": {
                        **inventory_base["hosts"],
                        "R": {
                            **inventory_base["hosts"]["R"],
                            "platform": platform,
                            "port": [10000, 10000+hosts-1] if hosts > 1 else 10000
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
                    "port": 10000+i
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
                        with open(f"ssh2_python/{platform}_{hosts}.csv", "a+", encoding="utf-8") as file:
                            writer = csv.writer(file)
                            writer.writerow([min_connection, max_connection, avg_connection, 
                                            min_command, max_command, avg_command, 
                                            min_disconnection, max_disconnection, avg_disconnection])

if __name__ == "__main__":
    p1 = multiprocessing.Process(target=python_netmiko_test)
    # p2 = multiprocessing.Process(target=python_scrapli_test)
    # p3 = multiprocessing.Process(target=python_paramiko_test)
    # p4 = multiprocessing.Process(target=python_asyncssh_test)
    # p5 = multiprocessing.Process(target=python_ssh2_test)

    p1.start()
    # p2.start()
    # p3.start()
    # p4.start()
    # p5.start()

    p1.join()
    # p2.join()
    # p3.join()
    # p4.join()
    # p5.join()

    print("Done!")
