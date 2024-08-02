from netmiko import ConnectHandler
from ntc_templates.parse import parse_output
import time

credentials = {
    'username': 'admin',
    'password': 'admin',
    'host': 'localhost',
    'port': 9000,
    'device_type': 'huawei_smartax',
}

onts = []
port = 0
with ConnectHandler(**credentials) as conn:
    results = []
    with ConnectHandler(**credentials) as conn:
        conn.enable()
        conn.config_mode()
        conn.send_command("interface gpon 0/0", auto_find_prompt=False)
        conn.find_prompt()
        output = conn.send_command(f"display ont info {port}")
        parsed_output = parse_output(
            platform='huawei_smartax',
            command=f"display ont info {port}",
            data=output
        )
        raw_output = conn.send_command(f"display ont optical-info {port} all")
        optical_output = parse_output(
            platform='huawei_smartax',
            command=f"display ont optical-info {port} all",
            data=raw_output
        )
        for ont in parsed_output:
            time.sleep(0.01)
            raw_output = conn.send_command(f"display ont gemport {port} ontid {ont['ont_id']}")
            gem_output = parse_output(
                platform='huawei_smartax',
                command=f"display ont gemport {port} ontid {ont['ont_id']}",
                data=raw_output
            )
            vlan_output = []
            time.sleep(0.01)
            for j in range(1, 5):
                raw_output = conn.send_command(f"display ont port vlan {port} {ont['ont_id']} byport eth {j}")
                vlan_output += parse_output(
                    platform='huawei_smartax',
                    command=f"display ont port vlan {port} {ont['ont_id']} byport eth {j}",
                    data=raw_output
                )
            time.sleep(0.01)
            raw_output = conn.send_command(f"display ont snmp-profile {port} all")
            snmp_output = parse_output(
                platform='huawei_smartax',
                command=f"display ont snmp-profile {port} all",
                data=raw_output
            )
            voltage = next((item for item in optical_output if item["ont_id"] == ont["ont_id"]), None)
            results.append({
                "fsp": f"0/0/{port}",
                "ont": ont["ont_id"],
                "sn": ont["serial_number"],
                "gem": gem_output,
                "vlan": vlan_output,
                "snmp": snmp_output,
                "registered": True,
                "voltage": voltage["voltage"]
            })
    onts = results[0]
print(onts)