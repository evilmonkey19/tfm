#!/bin/bash

# Define the device names and numbers
device_names=('brocade_netiron' 'ericsson_ipos' 'extreme_exos' 'dell_force10' 'cisco_s300' 'eltex' 'juniper_junos' 'allied_telesis_awplus' 'hp_procurve' 'aruba_os' 'cisco_ftd' 'huawei_smartax' 'vyatta_vyos' 'huawei_vrp' 'alcatel_aos' 'arista_eos' 'cisco_xr' 'checkpoint_gaia' 'hp_comware' 'avaya_vsp' 'avaya_ers' 'ipinfusion_ocnos' 'cisco_asa' 'linux' 'alcatel_sros' 'ubiquiti_edgerouter' 'broadcom_icos' 'zyxel_os' 'cisco_nxos' 'dlink_ds' 'cisco_ios' 'ubiquiti_edgeswitch')
numbers=(128)

# Loop through each device name
for device_name in "${device_names[@]}"; do
    # Loop through each number
    for number in "${numbers[@]}"; do
        # Construct the new filename, replacing spaces with underscores and appending the number
        new_filename="${device_name}_${number}.csv"
        # Copy results.csv to the netmiko folder with the new filename
        cp results.csv "paramiko/${new_filename}"
    done
done