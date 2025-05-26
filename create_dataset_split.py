import os
import json
import random
from pathlib import Path
from collections import defaultdict

def create_dataset_split(base_path, output_json):
    # Create base directory if it doesn't exist
    base_path = Path(base_path)
    base_path.mkdir(parents=True, exist_ok=True)
    
    # Dictionary to store files by their parent folder
    folder_files = defaultdict(list)
    
    # Get all files in all subdirectories
    for file_path in base_path.rglob("*.json"):  # Using rglob for recursive search
        # Get the parent folder name (e.g., "9999" from "data_process/abc_parsed/9999/...")
        parent_folder = file_path.parent.parent.name
        folder_files[parent_folder].append(str(file_path))  # Convert Path to string for JSON serialization
    
    # Create dataset structure
    dataset = {
        "train": [],
        "val": [],
        "test": [],
        "metadata": {
            "total_folders": len(folder_files),
            "total_files": sum(len(files) for files in folder_files.values()),
            "folders": {}
        }
    }
    
    # Process each folder
    for folder, files in folder_files.items():
        # Shuffle files in this folder
        random.shuffle(files)
        
        # Calculate split indices for this folder
        total_files = len(files)
        train_size = int(total_files * 0.6)
        val_size = int(total_files * 0.2)
        
        # Split the files
        train_files = files[:train_size]
        val_files = files[train_size:train_size + val_size]
        test_files = files[train_size + val_size:]
        
        # Add to main dataset
        dataset["train"].extend(train_files)
        dataset["val"].extend(val_files)
        dataset["test"].extend(test_files)
        
        # Add folder metadata
        dataset["metadata"]["folders"][folder] = {
            "total_files": total_files,
            "train_size": len(train_files),
            "val_size": len(val_files),
            "test_size": len(test_files)
        }
    
    # Update overall metadata
    dataset["metadata"]["train_size"] = len(dataset["train"])
    dataset["metadata"]["val_size"] = len(dataset["val"])
    dataset["metadata"]["test_size"] = len(dataset["test"])
    
    # Save to JSON file
    output_path = Path(output_json)
    with output_path.open('w') as f:
        json.dump(dataset, f, indent=2)
    
    # Print summary
    print(f"Dataset split created and saved to {output_path}")
    print(f"Total folders: {len(folder_files)}")
    print(f"Total files: {dataset['metadata']['total_files']}")
    print(f"Train set: {dataset['metadata']['train_size']} files")
    print(f"Validation set: {dataset['metadata']['val_size']} files")
    print(f"Test set: {dataset['metadata']['test_size']} files")

if __name__ == "__main__":
    base_path = Path("data_process/abc_parsed")
    output_json = "dataset_split.json"
    create_dataset_split(base_path, output_json) 