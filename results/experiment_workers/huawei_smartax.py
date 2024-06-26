import os
from fakenos import FakeNOS
from config_generator import generate_config

HOSTNAME = os.getenv("HOSTNAME", "OLT")
PORT = int(os.getenv("PORT", 9000))

inventory = {
    "hosts": {
        HOSTNAME: {
            "username": "admin",
            "password": "admin",
            "port": 9000,
            "platform": "huawei_smartax",
            "configuration_file": f"config.yaml"
        }
    }
}

configurations = generate_config(f'config.yaml')

with FakeNOS(inventory=inventory) as net:
    try:
        while True:
            pass
    except KeyboardInterrupt:
        pass
