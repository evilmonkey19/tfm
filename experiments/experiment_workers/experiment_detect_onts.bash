#!/bin/bash

n_sites=(1 2 3 4 5 6 7 8 9 10)
for i in "${n_sites[@]}"
do
    echo "i value: $i"
    python generate_scenario.py $i
    docker compose up -d --build
    sleep 60
    docker compose down 
    
done
