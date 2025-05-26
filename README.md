# Generative-Design-Module

A powerful generative design system that creates CAD-compatible part designs while satisfying physical constraints. This module leverages advanced machine learning techniques to generate optimized mechanical components that meet specified requirements.

## Features

- Generative design of CAD-compatible parts
- Physical constraint satisfaction
- Optimization for mechanical properties
- Integration with CAD software
- Customizable design parameters
- Export to standard CAD formats

## Prerequisites

- Python 3.8+
- CAD software (e.g., Fusion 360, SolidWorks)
- Required Python packages (see requirements.txt)
- 7-Zip for data extraction:
  - Windows: Install from https://www.7-zip.org/
  - Linux: `sudo apt-get install p7zip-full`
  - macOS: `brew install p7zip`

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Generative-Design-Module.git
cd Generative-Design-Module
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Data Pipeline

### 1. Data Download

To download the required STEP files for training and testing:

1. Create a directory for STEP files:
```bash
mkdir step
```

2. Download the files using parallel processing:
```bash
cat step_v00.txt | xargs -n 2 -P 8 sh -c 'wget --no-check-certificate $0 -O step/$1'
```

This command will:
- Read URLs and filenames from step_v00.txt
- Download files in parallel using 8 processes
- Save files in the 'step' directory
- Skip SSL certificate verification for faster downloads

Note: Make sure you have sufficient disk space and a stable internet connection before downloading.

### 2. Data Extraction

After downloading, extract the .7z archive files:

1. Create a directory for extracted files:
```bash
mkdir -p abc_subset
```

2. Run the extraction script:
```python
import os

step_dir = "step"
meta_dir = "abc_subset"
sevenz_files = [f for f in os.listdir(step_dir) if f.endswith(".7z")]
print(f"Found {len(sevenz_files)} .7z files")

# Extract all .7z files
for file in sevenz_files:
    archive_path = os.path.join(step_dir, file)
    print(f"Extracting: {file}")
    os.system(f'7z x "{archive_path}" -o"{meta_dir}/extracted" -y')
```

### 3. Data Preprocessing

To preprocess the extracted data:

1. Navigate to the data processing directory:
```bash
cd data/process
```

2. Run the preprocessing script:
```bash
for i in $(seq 0 4)
do
    timeout 1000 python process_brep.py --input ../abc_subset --interval $i --option 'abc'
    pkill -f 'python process_brep.py' # cleanup after each run
done
```

Parameters:
- `--input`: Path to the extracted data directory
- `--interval`: Processing interval (specify a value for $i)
- `--option`: Dataset option (set to 'abc' for ABC dataset)

### 4. Data Deduplication

To remove duplicate CAD models and components:

1. Deduplicate CAD models:
```bash
python deduplicate_cad.py --data abc_parsed --bit 6 --option 'abc'
```

2. Deduplicate surfaces and edges:
```bash
# Deduplicate surfaces
python deduplicate_surfedge.py --data abc_parsed --list abc_data_split_6bit.pkl --bit 6 --option 'abc'

# Deduplicate edges
python deduplicate_surfedge.py --data abc_parsed --list abc_data_split_6bit.pkl --bit 6 --edge --option 'abc'
```

Parameters:
- `--data`: Path to the parsed data directory
- `--bit`: Bit precision for deduplication
- `--list`: Path to the data split list file
- `--edge`: Flag to process edges instead of surfaces
- `--option`: Dataset option (set to 'abc' for ABC dataset)

## Training Pipeline

### 1. VAE Training

The system uses Variational Autoencoders (VAE) to learn surface and edge representations. There are two separate training processes:

1. Surface VAE Training:
```bash
python vae.py --data data_process/abc_parsed \
    --train_list data_process/abc_data_split_6bit_surface.pkl \
    --val_list data_process/abc_data_split_6bit.pkl \
    --option surface --gpu 0 --env abc_vae_surf --train_nepoch 2 --data_aug
```

2. Edge VAE Training:
```bash
python vae.py --data data_process/abc_parsed \
    --train_list data_process/abc_data_split_6bit_edge.pkl \
    --val_list data_process/abc_data_split_6bit.pkl \
    --option edge --gpu 0 --env abc_vae_edge --train_nepoch 2 --data_aug
```

Training Parameters:
- `--data`: Path to the parsed data directory
- `--train_list`: Path to the training data split file
- `--val_list`: Path to the validation data split file
- `--option`: Training type ('surface' or 'edge')
- `--gpu`: GPU device ID to use
- `--env`: Environment name for logging
- `--train_nepoch`: Number of training epochs
- `--data_aug`: Enable data augmentation

### 2. Latent Diffusion Model (LDM) Training

The system uses Latent Diffusion Models for generating CAD components. There are four different training configurations:

1. Surface Position LDM:
```bash
python ldm.py --data data_process/abc_parsed \
    --list data_process/abc_data_split_6bit.pkl --option surfpos --gpu 0 \
    --env abc_ldm_surfpos --train_nepoch 2 --test_nepoch 2 --save_nepoch 300 \
    --max_face 50 --max_edge 30
```

2. Surface Z-Space LDM:
```bash
python ldm.py --data data_process/abc_parsed \
    --list data_process/abc_data_split_6bit.pkl --option surfz \
    --surfvae proj_log/abc_vae_surf.pt --gpu 0 \
    --env abc_ldm_surfz --train_nepoch 300 --batch_size 256 \
    --max_face 50 --max_edge 30
```

3. Edge Position LDM:
```bash
python ldm.py --data data_process/abc_parsed \
    --list data_process/abc_data_split_6bit.pkl --option edgepos \
    --surfvae proj_log/abc_vae_surf.pt --gpu 0 \
    --env abc_ldm_edgepos --train_nepoch 300 --batch_size 64 \
    --max_face 50 --max_edge 30
```

4. Edge Z-Space LDM:
```bash
python ldm.py --data data_process/abc_parsed \
    --list data_process/abc_data_split_6bit.pkl --option edgez \
    --surfvae proj_log/abc_vae_surf.pt --edgevae proj_log/abc_vae_edge.pt --gpu 0 \
    --env abc_ldm_edgez --train_nepoch 300 --batch_size 64 \
    --max_face 50 --max_edge 30
```

LDM Training Parameters:
- `--data`: Path to the parsed data directory
- `--list`: Path to the data split file
- `--option`: Training type ('surfpos', 'surfz', 'edgepos', or 'edgez')
- `--surfvae`: Path to the trained surface VAE model
- `--edgevae`: Path to the trained edge VAE model
- `--gpu`: GPU device ID to use
- `--env`: Environment name for logging
- `--train_nepoch`: Number of training epochs
- `--test_nepoch`: Number of testing epochs
- `--save_nepoch`: Number of epochs between model saves
- `--batch_size`: Training batch size
- `--max_face`: Maximum number of faces per model
- `--max_edge`: Maximum number of edges per model

## Generation

### Sampling CAD Models

To generate new CAD models using the trained models:

```bash
python sample.py --mode abc
```

Parameters:
- `--mode`: Dataset mode (set to 'abc' for ABC dataset)

Note: Make sure all required models (VAE and LDM) are trained before running the sampling script. The generated models will be saved in the specified output directory.



