# %%
import os
import shutil

root = r'C:\Users\prart\CAD-GEN\BrepGen\data_process\abc_parsed_1'
dirs = os.listdir(root)

new_root = r'C:\Users\prart\CAD-GEN\BrepGen\data_process\abc_parsed_updated2\0001'
os.makedirs(new_root, exist_ok=True)

for folder in dirs:
    files = os.listdir(os.path.join(root, folder))
    assert len(files) == 1
    file = files[0]
    shutil.copy(os.path.join(root, folder, file), os.path.join(new_root, file))

# %%
