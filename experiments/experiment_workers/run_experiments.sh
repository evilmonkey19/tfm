#!/bin/bash

for i in {1..10}; do
    python generate_scenario.py $i misconfigurations
    for j in {1..10}; do
        cp events_log_template.csv events_log.csv
        python master.py
        mv events_log.csv event_log_${i}_${j}_only_misconfigurations.csv
    done
done

for i in {1..10}; do
    python generate_scenario.py $i errors
    for j in {1..10}; do
        cp events_log_template.csv events_log.csv
        python master.py
        mv events_log.csv event_log_${i}_${j}_only_errors.csv
    done
done
