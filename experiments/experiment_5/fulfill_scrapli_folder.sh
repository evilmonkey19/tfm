#!/bin/bash

# Define the device names and numbers
device_names=('cisco_nxos', 'cisco_xr', 'juniper_junos', 'arista_eos')
numbers=(1 2 4 8 16 32 64 128)

# Loop through each device name
for device_name in "${device_names[@]}"; do
    # Loop through each number
    for number in "${numbers[@]}"; do
        # Construct the new filename, replacing spaces with underscores and appending the number
        new_filename="${device_name}_${number}.csv"
        # Copy results.csv to the netmiko folder with the new filename
        cp results.csv "scrapli/${new_filename}"
    done
done