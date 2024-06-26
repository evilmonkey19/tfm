"""
Register an ONT in the OLT.
"""
import csv
from netmiko import ConnectHandler
from ntc_templates.parse import parse_output
from ttp import ttp

CREDENTIALS = {
    "host": "localhost",
    "username": "admin",
    "password": "admin",
    "device_type": "huawei_smartax",
    "port": 6000
}

registered_onts = []
def main():
    """ Main function """
    with ConnectHandler(**CREDENTIALS) as conn:
        conn.enable()
        conn.config_mode()
        conn.send_command("ont-srvprofile gpon profile-id 500 profile-name new_link", auto_find_prompt=False)
        conn.find_prompt()
        conn.send_command("ont-port pots 4 eth 4")
        output = conn.send_command("port vlan eth1 500")
        parsed_output = parse_output(platform="huawei_smartax", command="port vlan eth1 500", data=output)
        if int(parsed_output[0]["failed"]) != 0:
            raise Exception("Failed to set port vlan")
        conn.send_command("commit")
        conn.send_command("quit", auto_find_prompt=False)
        conn.find_prompt()
        conn.send_command("ont-lineprofile gpon profile-id 500 profile-name new_link", auto_find_prompt=False)
        conn.find_prompt()
        conn.send_command("tcont 4 dba-profile-id 5")
        conn.send_command("gem add 126 eth tcont 4")
        conn.send_command("gem mapping 126 0 vlan 500")
        conn.send_command("commit")
        conn.send_command("quit", auto_find_prompt=False)
        conn.find_prompt()
        conn.send_command("interface gpon 0/0", auto_find_prompt=False)
        conn.find_prompt()
        output = conn.send_command("display ont autofind 6")
        onts = parse_output(platform="huawei_smartax", command="display ont autofind 6", data=output)
        for ont in onts:
            ont_sn = ont.get("serial_number", "").split(" ")[0]
            output = conn.send_command(f"ont add 6 sn-auth {ont_sn} omci ont-lineprofile-id 500 ont-srvprofile-id 500 desc {ont_sn}")
            parsed_output = parse_output(platform="huawei_smartax", command=f"ont add 6 sn-auth {ont_sn} omci ont-lineprofile-id 500 ont-srvprofile-id 500 desc {ont_sn}", data=output)
            command = f"display ont info {parsed_output[0]['port_id']} {parsed_output[0]['ont_id']}"
            output = conn.send_command(command)
            parsed_output = parse_output(platform="huawei_smartax", command=command, data=output)
            # Parsing Tramas GEM
            parser = ttp(data=output, template="getting_gems.ttp")
            parser.parse()
            tconts = parser.result()[0][0]["tconts"]
            fields_to_register = ["fsp", "ont_id", "control_flag",
                               "run_state", "match_state", "management_mode",
                               "authentic_type", "serial_number", "description",
                               "line_profile_id", "line_profile_name",
                               "service_profile_id", "service_profile_name",
                               "number_pots", "number_eth", "number_tdm", "number_moca", "number_catv"]
            registered_ont = {field: parsed_output[0].get(field, None) for field in fields_to_register}
            registered_ont.update({"tconts": tconts})
            registered_onts.append(registered_ont)
        conn.send_command("quit", auto_find_prompt=False)
        conn.find_prompt()

    with open("results.csv", "w", newline="\n", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(registered_onts[0].keys())
        writer.writerows([row.values() for row in registered_onts])

if __name__ == "__main__":
    main()


