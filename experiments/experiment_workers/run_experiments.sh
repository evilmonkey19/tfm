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

#1_3
touch chaos_monkey_1_try_2_only_misconfigurations.csv
python generate_scenario.py 1 misconfigurations
cp events_log_template.csv events_log.csv
python master.py
mv events_log.csv event_log_1_3_only_misconfigurations.csv
#1_4
python generate_scenario.py 1 misconfigurations
cp events_log_template.csv events_log.csv
python master.py
mv events_log.csv event_log_1_4_only_misconfigurations.csv
#2_9
touch chaos_monkey_2_try_8_only_misconfigurations.csv
python generate_scenario.py 2 misconfigurations
cp events_log_template.csv events_log.csv
python master.py
mv events_log.csv event_log_2_9_only_misconfigurations.csv
#2_10
touch chaos_monkey_2_try_9_only_misconfigurations.csv
python generate_scenario.py 2 misconfigurations
cp events_log_template.csv events_log.csv
python master.py
mv events_log.csv event_log_2_10_only_misconfigurations.csv
#3_10
touch chaos_monkey_3_try_9_only_misconfigurations.csv
python generate_scenario.py 3 misconfigurations
cp events_log_template.csv events_log.csv
python master.py
mv events_log.csv event_log_3_10_only_misconfigurations.csv

