import csv
import os
from collections import defaultdict

input_file = 'all_mp4_scanned.csv'
output_file = 'duplicate_files.csv'

if not os.path.exists(input_file):
    print(f"Error: {input_file} not found.")
    exit(1)

hash_map = defaultdict(list)

with open(input_file, mode='r', encoding='utf-8', errors='replace') as f:
    # Try to detect if it's a standard CSV with headers
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    
    # Identify columns for Hash and Path
    hash_col = next((c for c in fieldnames if 'hash' in c.lower()), None)
    path_col = next((c for c in fieldnames if 'path' in c.lower()), None)

    if not hash_col or not path_col:
        print(f"Could not identify Hash or Path columns. Found: {fieldnames}")
        exit(1)

    for row in reader:
        h_val = row[hash_col].strip()
        p_val = row[path_col].strip()
        if h_val:
            hash_map[h_val].append(p_val)

# Filter for duplicates
duplicates = {h: paths for h, paths in hash_map.items() if len(paths) > 1}

if not duplicates:
    print("No duplicate hash values found.")
else:
    print(f"Found {len(duplicates)} duplicate hash groups. Writing to {output_file}...")
    with open(output_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['File Path', 'Hash', 'Size (Bytes)'])
        
        for h, paths in duplicates.items():
            for p in paths:
                # Get file size if file exists
                size = "Unknown/Not Found"
                if os.path.exists(p):
                    size = os.path.getsize(p)
                
                print(f"DUPLICATE: {p} (Hash: {h})")
                writer.writerow([p, h, size])
    print(f"\nScan complete. Duplicate list saved to {output_file}.")