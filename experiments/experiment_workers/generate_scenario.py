import yaml
import argparse

parser = argparse.ArgumentParser(description='Generate a scenario with a given number of workers and errors type')
parser.add_argument('workers', type=int, help='Number of workers')
parser.add_argument('errors', type=str, help='Type of errorsn [misconfigurations, errors, all, nothing]')
args = parser.parse_args()

i = args.workers+1
errors_type = args.errors

docker_compose = {
    "services": {
        "chaos_monkey": {
            "build": {
                "context": ".",
                "dockerfile": "chaos_monkey.Dockerfile",
            },
            "ports": ["3500:3500"],
            "networks": {
                **{f"worker{j}-net": {"ipv4_address": f"10.{j}.0.4"} for j in range(1,i)},
                **{f"huawei{j}-net": {"ipv4_address": f"192.168.{j}.4"} for j in range(1,i)},
            },
            "command": f"python chaos_monkey.py --only {errors_type}",
            "volumes":
                [
                    "/home/enric/tfm/experiments/experiment_workers:/app:rw",
                ]
        },
        "redis": {
            "image": "redis",
            "ports": ["6379:6379"],
            "networks": {f"worker{j}-net": {"ipv4_address": f"10.{j}.0.3"} for j in range(1,i)},
        },
        "rabbitmq": {
            "image": "rabbitmq:management",
            "ports": ["5672:5672", "15672:15672"],
            "networks": {f"worker{j}-net": {"ipv4_address": f"10.{j}.0.2"} for j in range(1,i)},
        },
        **{f"worker-site-{worker_site}":{
            "build": {
                "context": ".",
                "dockerfile": "worker.Dockerfile",
            },
            "command": "python worker.py",
            "environment": [
                f"RABBITMQ_IP=10.{worker_site}.0.2",
                f"REDIS_IP=10.{worker_site}.0.3",
                f"CHAOS_MONKEY_IP=10.{worker_site}.0.4",
                f"HUAWEI_SMARTAX_IP=192.168.{worker_site}.3",
                f"HOSTNAME=worker_site_{worker_site}",
                f"QUEUE_NAME=site_{worker_site}",
                f"CONFIGURATION_FILE=site_{worker_site}.yaml.j2",
            ],
            "depends_on": ["rabbitmq"],
            "networks": {
                f"worker{worker_site}-net": {"ipv4_address": f"10.{worker_site}.0.10"},
                f"huawei{worker_site}-net": {"ipv4_address": f"192.168.{worker_site}.2"},
            },
            "volumes":
                [
                    "/home/enric/tfm/experiments/experiment_workers:/app:rw",
                ]
        } for worker_site in range(1,i)},
        **{f"huawei_smartax-site-{worker_site}":{
            "build": {
                "context": ".",
                "dockerfile": "huawei_smartax.Dockerfile",
            },
            "command": "fastapi run fakenos-web.py",
            "depends_on": [f"worker-site-{worker_site}"],
            "environment": [f"HOSTNAME=huawei_smartax_site_{worker_site}", f"CONFIGURATION_FILE=site_{worker_site}.yaml.j2"],
            "networks": {
                f"huawei{worker_site}-net": {
                    "ipv4_address": f"192.168.{worker_site}.3"
                }
            },
        } for worker_site in range(1,i)},
    }
}

docker_compose["services"]["rabbitmq"]["networks"]["default"] = None

docker_compose["networks"] = {
    "default": {
        "driver": "bridge",
    },
    **{f"worker{worker_site}-net": {
        "driver": "bridge",
        "ipam": {
            "config": [
                {"subnet": f"10.{worker_site}.0.0/16"}
            ]
        }
    } for worker_site in range(1,i)},
    **{f"huawei{worker_site}-net": {
        "driver": "bridge",
        "ipam": {
            "config": [
                {"subnet": f"192.168.{worker_site}.0/24"}
            ]
        }
    } for worker_site in range(1,i)}
}

with open("docker-compose.yaml", "w") as f:
    yaml.dump(docker_compose, f)