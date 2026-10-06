import os
import argparse
import random
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET

def convert_voc_to_yolo(xml_dir, img_dir, out_base_dir, class_mapping):
    os.makedirs(out_base_dir, exist_ok=True)
    for split in ['train', 'val', 'test']:
        os.makedirs(os.path.join(out_base_dir, "images", split), exist_ok=True)
        os.makedirs(os.path.join(out_base_dir, "labels", split), exist_ok=True)

    xml_files = list(Path(xml_dir).glob("*.xml"))
    
    print(f"[INFO] Found {len(xml_files)} XML files in {xml_dir}.")
    
    converted = 0
    skipped = 0
    missing_img = 0
    
    valid_pairs = []
    
    for xml_file in xml_files:
        img_file = Path(img_dir) / (xml_file.stem + ".jpg")
        if not img_file.exists():
            img_file = Path(img_dir) / (xml_file.stem + ".jpeg")
        
        if not img_file.exists():
            missing_img += 1
            continue
            
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            size = root.find('size')
            if size is None:
                skipped += 1
                continue
                
            w = int(size.find('width').text)
            h = int(size.find('height').text)
            
            yolo_annotations = []
            
            for obj in root.findall('object'):
                class_name = obj.find('name').text
                if class_name not in class_mapping:
                    continue
                    
                class_id = class_mapping[class_name]
                xmlbox = obj.find('bndbox')
                xmin = float(xmlbox.find('xmin').text)
                xmax = float(xmlbox.find('xmax').text)
                ymin = float(xmlbox.find('ymin').text)
                ymax = float(xmlbox.find('ymax').text)
                
                # YOLO format: class_id center_x center_y width height (normalized)
                b_center_x = (xmin + xmax) / 2.0 / w
                b_center_y = (ymin + ymax) / 2.0 / h
                b_width = (xmax - xmin) / w
                b_height = (ymax - ymin) / h
                
                yolo_annotations.append(f"{class_id} {b_center_x:.6f} {b_center_y:.6f} {b_width:.6f} {b_height:.6f}")
                
            if yolo_annotations:
                valid_pairs.append((img_file, xml_file, yolo_annotations))
            else:
                skipped += 1
                
        except Exception as e:
            print(f"[ERROR] Failed to process {xml_file.name}: {e}")
            skipped += 1
            
    print(f"[INFO] Total valid image/annotation pairs: {len(valid_pairs)}")
    print(f"[INFO] Missing images for XMLs: {missing_img}")
    print(f"[INFO] Skipped (invalid XML or no mapped classes): {skipped}")
    
    # Shuffle and split
    random.seed(42)
    random.shuffle(valid_pairs)
    
    total = len(valid_pairs)
    train_end = int(total * 0.8)
    val_end = train_end + int(total * 0.1)
    
    splits = {
        'train': valid_pairs[:train_end],
        'val': valid_pairs[train_end:val_end],
        'test': valid_pairs[val_end:]
    }
    
    box_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    total_boxes = 0
    
    print("\n[SPLIT REPORT]")
    for split_name, items in splits.items():
        print(f"{split_name}: {len(items)} images")
        
        for img_path, xml_path, annotations in items:
            # Copy image
            dest_img = os.path.join(out_base_dir, "images", split_name, img_path.name)
            shutil.copy2(img_path, dest_img)
            
            # Write YOLO labels
            dest_txt = os.path.join(out_base_dir, "labels", split_name, img_path.stem + ".txt")
            with open(dest_txt, "w") as f:
                f.write("\n".join(annotations))
                
            for ann in annotations:
                cid = int(ann.split()[0])
                box_counts[cid] += 1
                total_boxes += 1
                
        converted += len(items)
        
    print("\n[CLASS DISTRIBUTION]")
    print(f"Total Bounding Boxes: {total_boxes}")
    for k, v in class_mapping.items():
        print(f"{k} (Class {v}): {box_counts[v]}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--xml_dir", type=str, required=True, help="Path to India annotations")
    parser.add_argument("--img_dir", type=str, required=True, help="Path to India images")
    parser.add_argument("--out_dir", type=str, required=True, help="Base output dataset dir (e.g. datasets/RDD2020)")
    args = parser.parse_args()
    
    mapping = {
        "D00": 0, # Longitudinal Crack
        "D10": 1, # Transverse Crack
        "D20": 2, # Alligator Crack
        "D40": 3  # Pothole
    }
    
    convert_voc_to_yolo(args.xml_dir, args.img_dir, args.out_dir, mapping)
