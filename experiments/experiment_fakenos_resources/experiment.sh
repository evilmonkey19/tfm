#!/bin/bash

platforms=(
    'alcatel_aos' 'alcatel_sros' 'allied_telesis_awplus' 'arista_eos' 'aruba_os' 'avaya_ers' 'avaya_vsp' 'broadcom_icos' 'brocade_netiron' 'checkpoint_gaia' 'cisco_asa' 'cisco_ftd' 'cisco_ios' 'cisco_nxos' 'cisco_s300' 'cisco_xr' 'dell_force10' 'dlink_ds' 'eltex' 'ericsson_ipos' 'extreme_exos' 'hp_comware' 'hp_procurve' 'huawei_smartax' 'huawei_vrp' 'ipinfusion_ocnos' 'juniper_junos' 'linux' 'ubiquiti_edgerouter' 'ubiquiti_edgeswitch' 'vyatta_vyos' 'zyxel_os'
)

n_hosts=(
    1 2 4 8 16 32 64 128
)

for n in "${n_hosts[@]}"; do
    for ((i=0; i<100; i++)); do
        for platform in "${platforms[@]}"; do
            python script.py "$platform" "$n"
        done
    done
done