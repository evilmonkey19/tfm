import yaml, csv

total_mismatchs = 0
with open("tfm/na_vs_manual/experiment_1/manual_results/results_1.csv", "r", encoding="utf-8") as file, \
    open("tfm/na_vs_manual/experiment_1/configurations/real/config_experiment_1.yaml", "r", encoding="utf-8") as real_file:
    csv_reader = csv.reader(file, delimiter=',')
    real_services = yaml.safe_load(real_file.read())["services"]
    next(csv_reader)  # Skip the first row (titles)
    for row, real_service in zip(csv_reader, real_services):
        detected_service = {
            "network_service": row[0],
            "port": int(row[1]),
            "state": row[2]
        }
        if detected_service not in real_services:
            total_mismatchs += 1
            continue
        if detected_service != real_service:
            total_mismatchs += 1