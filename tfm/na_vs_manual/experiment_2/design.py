import random
import yaml

with open("configurations/real/config_experiment.yaml", "r", encoding="utf-8") as file:
    values = yaml.safe_load(file.read())
    for board in values["frames"][0]["slots"]:
        board["boardname"] = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890', k=8))
        online_offline = random.choice(["online", "offline", ""])
        if random.random() < 0.1:
            board["subtype0"] = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890', k=4))
        if random.random() < 0.1:
            board["subtype1"] = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890', k=4))
        board["status"] = random.choice(["Standby_failed", "Active", "Normal", "Standby", "Failed", ""])
    with open(f"configurations/real/config_experiment_.yaml", "w", encoding="utf-8") as file:
        file.write(yaml.dump(values))