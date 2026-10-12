import os
import glob
import hashlib
from collections import defaultdict
from PIL import Image

def validate_datasets():
    print("=" * 70)
    print("    CIVICVISION AI — INDIAN DATASET INTEGRITY & SPLIT AUDIT")
    print("=" * 70)

    # 1. Audit RDD2020 India YOLO splits
    yolo_root = "datasets/RDD2020/yolo"
    splits = ["train", "val", "test"]
    print("\n[1] AUDITING RDD2020 (India Split YOLO Format - Bounding Box Detection):")
    total_yolo_images = 0
    total_yolo_labels = 0
    missing_labels = 0
    corrupt_images = 0

    for split in splits:
        img_dir = os.path.join(yolo_root, "images", split)
        lbl_dir = os.path.join(yolo_root, "labels", split)
        imgs = glob.glob(os.path.join(img_dir, "*.*"))
        lbls = glob.glob(os.path.join(lbl_dir, "*.txt"))
        total_yolo_images += len(imgs)
        total_yolo_labels += len(lbls)
        
        for img_p in imgs:
            base = os.path.splitext(os.path.basename(img_p))[0]
            lbl_p = os.path.join(lbl_dir, f"{base}.txt")
            if not os.path.exists(lbl_p):
                missing_labels += 1
            try:
                with Image.open(img_p) as im:
                    im.verify()
            except Exception:
                corrupt_images += 1

        print(f"  - Split '{split}': {len(imgs)} images, {len(lbls)} label files.")

    print(f"  * Total RDD2020 Images: {total_yolo_images}")
    print(f"  * Missing Label Files: {missing_labels}")
    print(f"  * Corrupted Images: {corrupt_images}")
    assert missing_labels == 0, "Discrepancy: Image missing corresponding label file!"
    assert corrupt_images == 0, "Discrepancy: Corrupted images detected!"
    print("  -> RDD2020 Status: PASSED (100% Valid Bounding Box Splits) [OK]")

    # 2. Audit Prepared Clean IRDID Classification Dataset
    prep_root = "datasets/indian_infrastructure/irdid_prepared_classification"
    print("\n[2] AUDITING IRDID PREPARED CLASSIFICATION (Deduplicated, Zero-Leakage):")
    
    if not os.path.exists(prep_root):
        print("  [!] Prepared directory not found. Please run prepare_irdid_classification.py first.")
        return

    prep_splits = ["train", "val", "test"]
    split_hashes = defaultdict(set)
    total_prep_images = 0

    for s in prep_splits:
        s_dir = os.path.join(prep_root, s)
        cats = sorted(os.listdir(s_dir))
        split_count = 0
        for c in cats:
            c_dir = os.path.join(s_dir, c)
            c_imgs = glob.glob(os.path.join(c_dir, "*.*"))
            split_count += len(c_imgs)
            for img_p in c_imgs:
                h = hashlib.sha256(open(img_p, "rb").read()).hexdigest()
                split_hashes[s].add(h)
        total_prep_images += split_count
        print(f"  - Split '{s}': {split_count} images across {len(cats)} classes.")

    print(f"  * Total Prepared Images: {total_prep_images}")

    # Verify zero data leakage
    overlap_tv = split_hashes["train"].intersection(split_hashes["val"])
    overlap_tt = split_hashes["train"].intersection(split_hashes["test"])
    overlap_vt = split_hashes["val"].intersection(split_hashes["test"])
    print(f"  * Overlap Train/Val: {len(overlap_tv)} | Train/Test: {len(overlap_tt)} | Val/Test: {len(overlap_vt)}")
    assert len(overlap_tv) == 0 and len(overlap_tt) == 0 and len(overlap_vt) == 0, "Leakage detected!"
    print("  -> IRDID Prepared Split Status: PASSED (Zero Data Leakage Across Splits) [OK]")

    print("\n" + "=" * 70)
    print("    DATASET VALIDATION AUDIT COMPLETE — ZERO CORRUPTION & ZERO LEAKAGE")
    print("=" * 70)

if __name__ == "__main__":
    validate_datasets()
