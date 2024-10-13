import csv
import re

misconfigurations = []
event_log = []

with open("chaos_monkey_1_try_1_only_misconfigurations.csv") as f:
    reader = csv.reader(f)
    _misconfigurations = list(reader)
    del _misconfigurations[0]
    del _misconfigurations[-1]
    unregistering_pattern = r'Unregistering (\S+) from \S+'
    for misconfiguration in _misconfigurations:
        if re.search(unregistering_pattern, misconfiguration[1]):
            misconfigurations.append({
                "type": "unregistered",
                "sn": re.search(unregistering_pattern, misconfiguration[1]).group(1),
            })
    s_vlan_pattern = r'Changing s vlan for (\S+) from \S+'
    for misconfiguration in _misconfigurations:
        if re.search(s_vlan_pattern, misconfiguration[1]):
            misconfigurations.append({
                "type": "s_vlan",
                "sn": re.search(s_vlan_pattern, misconfiguration[1]).group(1),
            })
    c_vlan_pattern = r'Changing c vlan for (\S+) from \S+'
    for misconfiguration in _misconfigurations:
        if re.search(c_vlan_pattern, misconfiguration[1]):
            misconfigurations.append({
                "type": "c_vlan",
                "sn": re.search(c_vlan_pattern, misconfiguration[1]).group(1),
            })
    vlan_type_pattern = r'Changing vlan type for (\S+) from \S+'
    for misconfiguration in _misconfigurations:
        if re.search(vlan_type_pattern, misconfiguration[1]):
            misconfigurations.append({
                "type": "vlan_type",
                "sn": re.search(vlan_type_pattern, misconfiguration[1]).group(1),
            })
    snmp_pattern = r'Changing snmp profile for (\S+) from \S+'
    for misconfiguration in _misconfigurations:
        if re.search(snmp_pattern, misconfiguration[1]):
            misconfigurations.append({
                "type": "snmp_profile",
                "sn": re.search(snmp_pattern, misconfiguration[1]).group(1),
            })
    gemport_pattern = r'Changing gemport for (\S+) from \S+'
    for misconfiguration in _misconfigurations:
        if re.search(gemport_pattern, misconfiguration[1]):
            misconfigurations.append({
                "type": "gemport",
                "sn": re.search(gemport_pattern, misconfiguration[1]).group(1),
            })


with open("event_log_1_1_only_misconfigurations.csv") as f:
    reader = csv.reader(f)
    _event_log = list(reader)
    del _event_log[0]
    for event in _event_log:
        if event[3] == "fixed":
            continue
        if event[4] == "service changed":
            continue
        event_log.append({
            "sn": event[5],
            "type": event[4],
        })

unmatched = []
for misconfiguration in misconfigurations:
    found = False
    for event in event_log:
        if misconfiguration["sn"] == event["sn"] and misconfiguration["type"] == event["type"]:
            found = True
            break
    if not found:
        unmatched.append(misconfiguration)

print("Unmatched misconfigurations:")
for misconfiguration in unmatched:
    print(misconfiguration)
