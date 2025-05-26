import math
import pickle 
import argparse
import os
from tqdm import tqdm
from hashlib import sha256
from convert_utils import *

parser = argparse.ArgumentParser()
parser.add_argument("--data", type=str, help="Data folder path", required=True)
parser.add_argument("--bit",  type=int, help='Deduplicate precision')
parser.add_argument("--option", type=str, choices=['abc', 'deepcad', 'furniture'], default='abc', 
                    help="Choose between dataset option [abc/deepcad/furniture] (default: abc)")
parser.add_argument("--debug", action="store_true", help="Enable debug mode")
args = parser.parse_args()

# Add debug option
debug_mode = args.debug

if args.option == 'deepcad': 
    OUTPUT = f'deepcad_data_split_{args.bit}bit.pkl'
elif args.option == 'abc': 
    OUTPUT = f'abc_data_split_{args.bit}bit.pkl'
else:
    OUTPUT = f'furniture_data_split_{args.bit}bit.pkl'

# Load all STEP folders
if args.option == 'furniture':
    train, val_path, test_path = load_furniture_pkl(args.data)
else:
    train, val_path, test_path = load_abc_pkl(args.data, args.option=='deepcad')

# Check data structure if in debug mode
if debug_mode:
    print(f"First 5 training IDs: {train[:5]}")
    if len(train) > 0:
        example_uid = train[0]
        example_folder = str(math.floor(int(example_uid.split('.')[0])/10000)).zfill(4)
        example_path = os.path.join(args.data, example_folder, example_uid)
        print(f"Example path calculation: {example_uid} -> folder {example_folder} -> {example_path}")
        print(f"Does this path exist? {os.path.exists(example_path)}")
        
        # Check if the folder structure is as expected
        folder_path = os.path.join(args.data, example_folder)
        print(f"Does folder {folder_path} exist? {os.path.exists(folder_path)}")
        if os.path.exists(folder_path):
            print(f"Files in {folder_path}: {os.listdir(folder_path)[:10]}")

# Remove duplicate for the training set 
train_path = []
unique_hash = set()
total = 0

for path_idx, uid in tqdm(enumerate(train)):
    total += 1

    # Improved path construction with error handling
    try:
        # Load pkl data
        # Load pkl data
        if args.option == 'furniture':
            path = os.path.join(args.data, uid)
        else:
            folder = uid.split('.')[0][:4]  # Take the first 4 characters for the folder
            path = os.path.join(args.data, folder, uid)
                    
        # Check if file exists before attempting to open
        if not os.path.exists(path):
            if debug_mode:
                print(f"Warning: File not found: {path}")
                # Try to locate file with similar name
                folder_path = os.path.join(args.data, folder)
                if os.path.exists(folder_path):
                    similar_files = [f for f in os.listdir(folder_path) if f.startswith(uid.split('.')[0][:4])]
                    if similar_files:
                        print(f"Similar files found: {similar_files}")
            continue
            
        with open(path, "rb") as file:
            data = pickle.load(file) 

        # Hash the surface sampled points
        surfs_wcs = data['surf_wcs']
        surf_hash_total = []
        for surf in surfs_wcs:
            np_bit = real2bit(surf, n_bits=args.bit).reshape(-1, 3)  # bits
            data_hash = sha256(np_bit.tobytes()).hexdigest()
            surf_hash_total.append(data_hash)
        surf_hash_total = sorted(surf_hash_total)
        data_hash = '_'.join(surf_hash_total)

        # Save non-duplicate shapes
        prev_len = len(unique_hash)
        unique_hash.add(data_hash)  
        if prev_len < len(unique_hash):
            train_path.append(uid)
        
        if path_idx % 2000 == 0:
            print(f"Progress: {path_idx}/{len(train)}, Unique: {len(unique_hash)}/{total} ({len(unique_hash)/total:.2f})")
            
    except Exception as e:
        if debug_mode:
            print(f"Error processing {uid}: {str(e)}")
        continue

# save data 
data_path = {
    'train': train_path,
    'val': val_path,
    'test': test_path,
}

print(f"Final statistics: {len(train_path)}/{len(train)} ({len(train_path)/len(train):.2f}) training samples kept after deduplication")
with open(OUTPUT, "wb") as tf:
    pickle.dump(data_path, tf)
print(f"Saved output to {OUTPUT}")