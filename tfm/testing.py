from netmiko import ConnectHandler
from ntc_templates.parse import parse_output

credentials = {
    "host": "127.0.0.1",
    "username": "user",
    "password": "user",
    "device_type": "huawei_smartax",
    "port": 6000,
}

with ConnectHandler(**credentials) as connection:
    command = "display ont info 0/2/0"
    output = connection.send_command(command)
    parsed_output = parse_output(platform="huawei_smartax", command=command, data=output)
    print(parsed_output[0]['sn']
