import csv
import os
import re

filenames = os.listdir('.')
filenames = [f for f in filenames if f.endswith('.csv')]
filenames_chaos_monkey = [f for f in filenames if f.startswith('chaos_monkey')]
filenames_event_log = [f for f in filenames if f.startswith('event_log')]

serial_number_pattern = re.compile(r'[A-Z0-9]{16}')

for f in filenames_event_log:
    matches = 0
    for f2 in filenames_chaos_monkey:
        with open(f, 'r') as file1:
            reader1 = csv.reader(file1)
            next(reader1)
            event_log = list(reader1)
        with open(f2, 'r') as file2:
            reader2 = csv.reader(file2)
            next(reader2)
            chaos_monkey = list(reader2)
        for row1 in event_log:
            if re.search(serial_number_pattern, row1[4]) is None:
                continue
            for row2 in chaos_monkey:
                if re.search(serial_number_pattern, row2[1]) is None:
                    continue
                if re.search(serial_number_pattern, row1[4]).group(0) == re.search(serial_number_pattern, row2[1]).group(0):
                    matches += 1
                    if matches > 20:
                        print(f'More than 20 matches found - {f} - {f2}')
                        break
            if matches > 20:
                break
        if matches > 20:
            break
    if matches < 20:
        print(f'Less than 20 matches found - {f}')
