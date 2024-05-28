"""
This is the script for the first experiment.
The intention of such script is to
test how long does it take to retrieve 
and store the information of all the ONTs
into nautobot.
"""
import csv
import random
import string
import time

from wonderwords import RandomSentence
from fakenos import FakeNOS
import yaml
from ntc_templates.parse import parse_output
from netmiko import ConnectHandler

s = RandomSentence()

def get_random_sn():
    """Returns a random serial number."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))

inventory = {
    "hosts": {
        "OLT": {
            "username": "user",
            "password": "user",
            "port": 6000,
            "nos": {
                "plugin": "tfm/huawei_smartax.py",
            },
            "configuration_file": "config.yaml",
        }
    }
}

for i in range(10):

    config = {
        "frames": [{
            "frame_id": 0,
            "slots": [
                {
                    "slotid": 0,
                    "boardname": "A123ABCD",
                    "status": "Normal",
                    "subtype0": "",
                    "subtype1": "",
                    "online_offline": "",
                },
                {
                    "slotid": 1,
                    "boardname": "",
                    "status": "",
                    "subtype0": "",
                    "subtype1": "",
                    "online_offline": "",
                },
                {
                    "slotid": 2,
                    "boardname": "H901GPSFE",
                    "status": "Normal",
                    "subtype0": "",
                    "subtype1": "",
                    "online_offline": "",
                    "ports": [[
                            {
                                "ont_id": i,
                                "sn": get_random_sn(),
                                "control_flag": random.choices(["active", "configuring"])[0],
                                "run_state": random.choices(["online", "offline"])[0],
                                "config_state": random.choices(["online", "normal", "failing"])[0],
                                "match_state": random.choices(["initial", "match", "mismatch"])[0],
                                "online_offline": random.choices(["online", "offline"])[0],
                                "protect_side": random.choices(["yes", "no"])[0],
                                "description": s.bare_bone_with_adjective()
                            } for i in range(random.randint(1,32))] for j in range(random.randint(1,16))]
                },
                {
                    "slotid": 3,
                    "boardname": "A123ABCD",
                    "status": "Active_normal",
                    "subtype0": "CPCF",
                    "subtype1": "",
                    "online_offline": "",
                },
                {
                    "slotid": 4,
                    "boardname": "A123ABCD",
                    "status": "Standby_failed",
                    "subtype0": "CPCF",
                    "subtype1": "",
                    "online_offline": "Offline",
                },
                {
                    "slotid": 5,
                    "boardname": "",
                    "status": "",
                    "subtype0": "",
                    "subtype1": "",
                    "online_offline": "",
                },
            ]
        }],
    }
    with open("config.yaml", "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True)


    with FakeNOS(inventory=inventory):
        with ConnectHandler(**credentials) as conn:
            output = conn.send_command("display ont info 0/2/0")
            parsed_output = parse_output(platform="huawei_smartax", command="display ont info 0/2/0", data=output)
            print(parsed_output)
        device = nautobot.dcim.devices.get(name="olt.cpd.internal")
        job = nautobot.extras.jobs.all()[-1]
        job_result = job.run(job_id=job.id, data={"device": device.id}, commit=True)
        while nautobot.extras.job_results.get(id=job_result.job_result.id).status.value in ["STARTED", 'PENDING', "RUNNING"]:
            time.sleep(1)


    real_total_onts: int = 0

    for frame in config["frames"]:
        for slot in frame["slots"]:
            if slot["boardname"] == "H901GPSFE":
                for port in slot["ports"]:
                    real_total_onts += len(port)

    detected_total_onts = len(nautobot.dcim.devices.filter(role=ont_role))

    with open("results/experiment_1.csv", "a+", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([real_total_onts, detected_total_onts, real_total_onts - detected_total_onts])
