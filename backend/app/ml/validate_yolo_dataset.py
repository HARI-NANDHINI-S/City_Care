import os
import yaml
import argparse
from pathlib import Path

def validate_yolo_dataset(yaml_path):
    print("====================================")
    print("RDD2020 INDIA DATASET VALIDATION")
    print("====================================")
    print(f"Validating YOLO dataset using config: {yaml_path}")
    if not os.path.exists(yaml_path):
        print(f"[ERROR] data.yaml not found at {yaml_path}")
        return False

    with open(yaml_path, 'r') as f:
        try:
            config = yaml.safe_load(f)
        except Exception as e:
            print(f"[ERROR] Could not parse yaml: {e}")
            return False

    base_dir = os.path.dirname(os.path.abspath(yaml_path))

    required_keys = ['train', 'val', 'nc', 'names']
    for key in required_keys:
        if key not in config:
            print(f"[ERROR] Missing '{key}' in data.yaml")
            return False

    print(f"Classes (nc={config['nc']}): {config['names']}")

    missing_images = 0
    missing_labels = 0
    invalid_labels = 0
    
    class_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    split_counts = {'train': 0, 'val': 0, 'test': 0}

    for split in ['train', 'val', 'test']:
        if split in config:
            img_dir = os.path.join(base_dir, config[split])
            lbl_dir = img_dir.replace("images", "labels")
            
            if not os.path.exists(img_dir):
                print(f"[ERROR] Split directory not found: {img_dir}")
                return False
                
            images = list(Path(img_dir).rglob("*.jpg")) + list(Path(img_dir).rglob("*.png"))
            split_counts[split] = len(images)
            
            for img in images:
                label_file = Path(lbl_dir) / (img.stem + ".txt")
                if not label_file.exists():
                    missing_labels += 1
                    continue
                    
                with open(label_file, "r") as f:
                    lines = f.readlines()
                    for line in lines:
                        parts = line.strip().split()
                        if len(parts) != 5:
                            invalid_labels += 1
                            continue
                        try:
                            cid = int(parts[0])
                            if cid not in [0, 1, 2, 3]:
                                invalid_labels += 1
                            else:
                                class_counts[cid] += 1
                        except:
                            invalid_labels += 1

    print("\nRDD2020 INDIA DATASET")
    print("-" * 21)
    print(f"Train images: {split_counts.get('train', 0)}")
    print(f"Val images: {split_counts.get('val', 0)}")
    print(f"Test images: {split_counts.get('test', 0)}\n")
    
    print(f"D00: {class_counts[0]}")
    print(f"D10: {class_counts[1]}")
    print(f"D20: {class_counts[2]}")
    print(f"D40: {class_counts[3]}\n")
    
    print(f"Invalid labels: {invalid_labels}")
    print(f"Missing labels: {missing_labels}")
    print(f"Missing images: {missing_images}\n")
    
    is_ready = sum(split_counts.values()) > 0 and sum(class_counts.values()) > 0
    print(f"Status: {'READY' if is_ready else 'NOT READY'}")
    return is_ready

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default="datasets/RDD2020/data.yaml")
    args = parser.parse_args()
    validate_yolo_dataset(args.data)
