import os
from fakenos import FakeNOS

HOSTNAME = os.getenv("HOSTNAME", "OLT")
PORT = int(os.getenv("PORT", "9000"))

inventory = {
    "hosts": {
        HOSTNAME: {
            "username": "admin",
            "password": "admin",
            "port": 9000,
            "platform": "huawei_smartax",
            "configuration_file": 'configuration.yaml.j2'
        }
    }
}

with FakeNOS(inventory=inventory) as net:
    try:
        while True:
            pass
    except KeyboardInterrupt:
        pass