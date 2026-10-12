import os
import glob
from collections import defaultdict

def report_class_distribution():
    print("=" * 70)
    print("      CIVICVISION AI — DETAILED CLASS DISTRIBUTION REPORT")
    print("=" * 70)

    # 1. RDD2020 Bounding Box Instances
    yolo_root = "datasets/RDD2020/yolo"
    class_names = {
        0: "D00 (Longitudinal Crack)",
        1: "D10 (Transverse Crack)",
        2: "D20 (Alligator Crack)",
        3: "D40 (Pothole)"
    }
    
    split_counts = {"train": defaultdict(int), "val": defaultdict(int), "test": defaultdict(int)}
    
    for split in ["train", "val", "test"]:
        lbl_dir = os.path.join(yolo_root, "labels", split)
        for lf in glob.glob(os.path.join(lbl_dir, "*.txt")):
            with open(lf, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if parts:
                        cls_id = int(parts[0])
                        split_counts[split][cls_id] += 1

    print("\n[RDD2020 INDIA SPLIT — BOUNDING BOX INSTANCE COUNTS (OBJECT DETECTION)]")
    print(f"{'Class Name':<30} | {'Train':<8} | {'Val':<8} | {'Test':<8} | {'Total':<8}")
    print("-" * 70)
    for cid in range(4):
        cname = class_names[cid]
        tr = split_counts["train"][cid]
        va = split_counts["val"][cid]
        te = split_counts["test"][cid]
        tot = tr + va + te
        print(f"{cname:<30} | {tr:<8} | {va:<8} | {te:<8} | {tot:<8}")

    # 2. Prepared IRDID Image Counts (Clean & Deduplicated)
    prep_root = "datasets/indian_infrastructure/irdid_prepared_classification"
    print("\n[IRDID PREPARED SPLIT — IMAGE COUNTS (IMAGE-LEVEL CLASSIFICATION ONLY)]")
    print(f"{'Folder / Category':<25} | {'Train':<8} | {'Val':<8} | {'Test':<8} | {'Total Clean':<12}")
    print("-" * 70)
    if os.path.exists(prep_root):
        train_cats = sorted(os.listdir(os.path.join(prep_root, "train")))
        for c in train_cats:
            tr = len(glob.glob(os.path.join(prep_root, "train", c, "*.*")))
            va = len(glob.glob(os.path.join(prep_root, "val", c, "*.*")))
            te = len(glob.glob(os.path.join(prep_root, "test", c, "*.*")))
            tot = tr + va + te
            print(f"{c:<25} | {tr:<8} | {va:<8} | {te:<8} | {tot:<12}")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    report_class_distribution()
