import os
import hashlib
from collections import defaultdict

def get_file_hash(filepath):
    """Calculate MD5 hash of a file in chunks."""
    hasher = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (PermissionError, OSError):
        return None

def find_duplicates():
    home_dir = os.path.expanduser('~')
    print(f'Scanning: {home_dir}')
    
    all_files_data = []
    hash_dict = defaultdict(list)
    
    for root, _, files in os.walk(home_dir):
        for file in files:
            if file.lower().endswith('.mp4'):
                full_path = os.path.join(root, file)
                file_hash = get_file_hash(full_path)
                
                if file_hash:
                    all_files_data.append((file_hash, full_path))
                    hash_dict[file_hash].append(full_path)

    # Sort all scanned files by hash value
    all_files_data.sort(key=lambda x: x[0])

    # Save list of all scanned files
    with open('all_mp4_scanned.csv', 'w', encoding='utf-8') as f:
        f.write('Hash,File_Path\n')
        for h, p in all_files_data:
            f.write(f'{h},{p}\n')

    # Save list of duplicates
    with open('duplicate_mp4_report.txt', 'w', encoding='utf-8') as f:
        f.write('DUPLICATE MP4 FILES REPORT\n')
        f.write('==========================\n\n')
        duplicates_found = False
        for h, paths in hash_dict.items():
            if len(paths) > 1:
                duplicates_found = True
                f.write(f'Hash: {h}\n')
                for p in paths:
                    f.write(f'  - {p}\n')
                f.write('\n')
        
        if not duplicates_found:
            f.write('No duplicates found.')

    print(f'Scan complete.')
    print(f'1. All files list: all_mp4_scanned.csv')
    print(f'2. Duplicate report: duplicate_mp4_report.txt')

if __name__ == '__main__':
    find_duplicates()