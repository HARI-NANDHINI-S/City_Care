import tarfile
import os
import shutil

archive_path = r'E:\City_Care\train.tar.gz'
target_dir = r'E:\City_Care\datasets\RDD2020'
india_target = os.path.join(target_dir, 'India')

if os.path.exists(india_target):
    print("India directory already exists. Removing it for clean extraction.")
    shutil.rmtree(india_target)

print("Extracting train/India from train.tar.gz...")

with tarfile.open(archive_path, "r:gz") as tar:
    members = tar.getmembers()
    india_members = [m for m in members if m.name.startswith('train/India/')]
    
    # We want to extract them such that train/India/ becomes datasets/RDD2020/India/
    # tarfile.extractall takes a path. If we just extract, it goes to datasets/RDD2020/train/India/
    tar.extractall(path=target_dir, members=india_members)

# Move datasets/RDD2020/train/India to datasets/RDD2020/India
extracted_india = os.path.join(target_dir, 'train', 'India')
if os.path.exists(extracted_india):
    shutil.move(extracted_india, india_target)
    # Cleanup empty train dir
    os.rmdir(os.path.join(target_dir, 'train'))
    print(f"Moved extracted files to {india_target}")
else:
    print(f"Failed to find {extracted_india}")

# Verify
img_dir = os.path.join(india_target, 'images')
xml_dir = os.path.join(india_target, 'annotations', 'xmls')

if not os.path.exists(xml_dir):
    xml_dir = os.path.join(india_target, 'annotations', 'xmls')
    if not os.path.exists(xml_dir):
        # some versions just have annotations
        xml_dir = os.path.join(india_target, 'annotations')

print("Extraction Verification:")
if os.path.exists(img_dir):
    print(f"Images: {len(os.listdir(img_dir))}")
if os.path.exists(xml_dir):
    print(f"XMLs: {len(os.listdir(xml_dir))}")
