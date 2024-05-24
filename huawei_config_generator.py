import random
import string

import yaml
from wonderwords import RandomSentence

s = RandomSentence()


random_sn = lambda: ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
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
                            "sn": random_sn(),
                            "control_flag": random.choices(["active", "configuring"])[0],
                            "run_state": random.choices(["online", "offline"])[0],
                            "config_state": random.choices(["online", "normal", "failing"])[0],
                            "match_state": random.choices(["initial", "match", "mismatch"])[0],
                            "online_offline": random.choices(["online", "offline"])[0],
                            "protect_side": random.choices(["yes", "no"])[0],
                            "description": s.bare_bone_with_adjective()

                        } for i in range(16)] for j in range(4)]
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

open("config.yaml", "w").write(yaml.dump(config))