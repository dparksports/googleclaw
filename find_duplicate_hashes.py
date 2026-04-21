import csv
import os
from collections import defaultdict

def check_duplicates():
    csv_file = 'all_mp4_scanned.csv'
    if not os.path.exists(csv_file):
        print(f'Error: {csv_file} not found.')
        return

    hash_map = defaultdict(list)
    
    with open(csv_file, mode='r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        # Identify hash and path columns dynamically
        hash_col = next((h for h in headers if 'hash' in h.lower()), None)
        path_col = next((h for h in headers if 'path' in h.lower()), None)

        if not hash_col or not path_col:
            print(f'Could not find hash or path columns. Headers found: {headers}')
            return

        for row in reader:
            h_val = row[hash_col]
            p_val = row[path_col]
            if h_val:
                hash_map[h_val].append(p_val)

    duplicates = {h: paths for h, paths in hash_map.items() if len(paths) > 1}

    if not duplicates:
        print('No duplicate hash values found.')
    else:
        print(f'Found {len(duplicates)} duplicate hash sets:\n')
        for h, paths in duplicates.items():
            print(f'Hash: {h}')
            for p in paths:
                full_path = os.path.abspath(p)
                size = 'Unknown (File Not Found)'
                if os.path.exists(full_path):
                    size = f'{os.path.getsize(full_path)} bytes'
                print(f'  - Path: {full_path}')
                print(f'    Size: {size}')
            print('-' * 50)

if __name__ == '__main__':
    check_duplicates()