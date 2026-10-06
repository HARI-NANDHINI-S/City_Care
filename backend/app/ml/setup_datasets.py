import os
import argparse
from pathlib import Path

def setup_datasets(base_dir):
    print("====================================")
    print("DATASET SETUP AND INSPECTION")
    print("====================================")
    
    datasets_dir = os.path.join(base_dir, "datasets")
    os.makedirs(datasets_dir, exist_ok=True)
    
    # 1. RDD2020 Check
    rdd_dir = os.path.join(datasets_dir, "RDD2020")
    print("\n[INSPECTING] RDD2020 Dataset")
    if not os.path.exists(rdd_dir):
        print(f"[-] Directory {rdd_dir} is missing.")
        os.makedirs(rdd_dir, exist_ok=True)
        print(f"[+] Created {rdd_dir}. Please place dataset files here.")
    else:
        print(f"[+] Directory {rdd_dir} exists.")
        
        # Check for archive files
        archives = list(Path(rdd_dir).glob("*.zip")) + list(Path(rdd_dir).glob("*.tar.gz"))
        if archives:
            print(f"[!] Found {len(archives)} archive file(s). Please extract them manually.")
            for arc in archives:
                print(f"    - {arc.name}")
                
        # Check subdirectories
        images_dir = os.path.join(rdd_dir, "images")
        labels_dir = os.path.join(rdd_dir, "labels")
        xml_dir = os.path.join(rdd_dir, "India", "Annotations") # common in raw RDD2020
        
        has_images = os.path.exists(images_dir) and any(os.scandir(images_dir))
        has_labels = os.path.exists(labels_dir) and any(os.scandir(labels_dir))
        has_xmls = os.path.exists(xml_dir) and any(os.scandir(xml_dir))
        
        if has_images:
            print("[+] Image directory populated.")
        if has_labels:
            print("[+] YOLO Label directory populated.")
        if has_xmls and not has_labels:
            print("[!] Found XML annotations. You need to run the conversion script: convert_rdd_to_yolo.py")
            
    # 2. Priority Dataset Check
    priority_dir = os.path.join(datasets_dir, "priority")
    print("\n[INSPECTING] Priority Dataset")
    if not os.path.exists(priority_dir):
        os.makedirs(priority_dir, exist_ok=True)
        print(f"[+] Created {priority_dir}.")
        
    csvs = list(Path(priority_dir).glob("*.csv"))
    if csvs:
        print(f"[+] Found {len(csvs)} CSV files.")
    else:
        print("[-] No priority CSV files found (except templates).")

    print("\n[SETUP] Dataset directories are prepared. Follow the manual action checklist to proceed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=str, default=".", help="Base project directory")
    args = parser.parse_args()
    setup_datasets(args.base)
