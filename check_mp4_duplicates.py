import csv
import os
from collections import defaultdict

def main():
    csv_file = 'all_mp4_scanned.csv'
    if not os.path.exists(csv_file):
        print(f"Error: '{csv_file}' not found in the current directory.")
        return

    hash_map = defaultdict(list)
    
    try:
        with open(csv_file, mode='r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            # Attempt to find relevant columns dynamically
            cols = {k.lower(): k for k in reader.fieldnames} if reader.fieldnames else {}
            hash_col = next((cols[k] for k in cols if 'hash' in k), None)
            path_col = next((cols[k] for k in cols if 'path' in k), None)
            size_col = next((cols[k] for k in cols if 'size' in k), None)

            if not hash_col:
                print("Error: Could not identify a 'hash' column in the CSV.")
                return

            for row in reader:
                h_val = row.get(hash_col)
                if h_val:
                    hash_map[h_val].append({
                        'path': row.get(path_col, 'Unknown Path'),
                        'size': row.get(size_col, 'Unknown Size')
                    })

        duplicates = {h: files for h, files in hash_map.items() if len(files) > 1}

        if not duplicates:
            print("No duplicate hash values found.")
        else:
            print(f"Found {len(duplicates)} sets of duplicate files:\n")
            for h, files in duplicates.items():
                print(f"HASH: {h}")
                for f_info in files:
                    print(f"  - Size: {f_info['size']} | Path: {f_info['path']}")
                print("-" * 60)

    except Exception as e:
        print(f"An error occurred while processing the CSV: {e}")

if __name__ == '__main__':
    main()