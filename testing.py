from netmiko import ConnectHandler
from ntc_templates.parse import parse_output

credentials = {
    "host": "localhost",
    "username": "user",
    "password": "user",
    "device_type": "huawei_smartax",
    "port": 6000,
}

with ConnectHandler(**credentials) as conn:
    output = conn.send_command("display ont info 0/2/0")
    parsed = parse_output(platform="huawei_smartax", command="display ont info 0/2/0", data=output)
    print(parsed)
    