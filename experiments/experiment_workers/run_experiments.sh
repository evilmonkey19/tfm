#!/bin/bash
# for i in {1..10}; do
#     python generate_scenario.py $i misconfigurations
#     for j in {1..10}; do
#         cp events_log_template.csv events_log.csv
#         python master.py
#         mv events_log.csv event_log_${i}_${j}_only_misconfigurations.csv
#     done
# done

# for i in {6..6}; do
#     python generate_scenario.py $i misconfigurations
#     for j in {4..4}; do
#         cp events_log_template.csv events_log.csv
#         python master.py
#         mv events_log.csv event_log_${i}_${j}_only_misconfigurations.csv 
#     done
# done

#7_5
touch chaos_monkey_7_try_4_only_errors.csv
python generate_scenario.py 7 errors
cp events_log_template.csv events_log.csv
python master.py
mv events_log.csv event_log_7_5_only_errors.csv