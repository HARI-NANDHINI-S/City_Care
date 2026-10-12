import os
import shutil
import random
import hashlib
from collections import defaultdict

def prepare_deduplicated_irdid_classification():
    print("=" * 70)
    print("  PREPARING DE-DUPLICATED IRDID CLASSIFICATION DATASET (ZERO LEAKAGE)")
    print("=" * 70)

    source_root = "Indian-Road-Damage-Infrastructure-Dataset/images"
    target_root = "datasets/indian_infrastructure/irdid_prepared_classification"
    
    if os.path.exists(target_root):
        print(f"Cleaning existing directory: {target_root}")
        shutil.rmtree(target_root)

    categories = [
        "broken_edges",        # Source concept: Broken Road Edges / Shoulder Damage
        "waterlogged_roads",   # Source concept: Waterlogged Roads
        "open_manholes",       # Source concept: Open Manholes
        "potholes",            # Source concept: Potholes
        "cracks",              # Source concept: Cracks
        "construction_zones"   # Source concept: Construction / Repair Zones
    ]

    # Step 1: Detect cross-category duplicate hashes to eliminate label ambiguity
    hash_to_categories = defaultdict(set)
    for cat in categories:
        src_cat_dir = os.path.join(source_root, cat)
        if not os.path.isdir(src_cat_dir):
            continue
        for f in os.listdir(src_cat_dir):
            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                fpath = os.path.join(src_cat_dir, f)
                h = hashlib.sha256(open(fpath, "rb").read()).hexdigest()
                hash_to_categories[h].add(cat)

    ambiguous_hashes = {h for h, cats in hash_to_categories.items() if len(cats) > 1}
    print(f"Found {len(ambiguous_hashes)} ambiguous image content hash(es) appearing across multiple categories.")

    # Step 2: Deduplicate within each category, excluding cross-category ambiguous files
    unique_images_by_cat = {}
    total_raw = 0
    total_unique = 0
    duplicate_copies = 0
    ambiguous_excluded = 0

    for cat in categories:
        src_cat_dir = os.path.join(source_root, cat)
        if not os.path.isdir(src_cat_dir):
            continue

        raw_files = sorted(os.listdir(src_cat_dir))
        total_raw += len(raw_files)
        
        seen_hashes = set()
        unique_files = []
        for f in raw_files:
            if not f.lower().endswith(('.jpg', '.jpeg', '.png')):
                continue
            fpath = os.path.join(src_cat_dir, f)
            h = hashlib.sha256(open(fpath, "rb").read()).hexdigest()
            if h in ambiguous_hashes:
                ambiguous_excluded += 1
                continue
            if h not in seen_hashes:
                seen_hashes.add(h)
                unique_files.append((f, fpath, h))
            else:
                duplicate_copies += 1

        unique_images_by_cat[cat] = unique_files
        total_unique += len(unique_files)
        print(f"  * Category '{cat}': raw={len(raw_files)}, unique_clean={len(unique_files)}")

    print(f"\nTotal raw images: {total_raw} | Unique clean images: {total_unique}")
    print(f"Filtered exact duplicate copies: {duplicate_copies} | Ambiguous cross-category copies excluded: {ambiguous_excluded}")

    # Step 3: Partition unique images: 70% train, 15% val, 15% test
    # Deterministic seed for exact reproducibility
    random.seed(42)
    split_summary = defaultdict(lambda: defaultdict(int))
    split_hashes = defaultdict(set)

    for cat, items in unique_images_by_cat.items():
        random.shuffle(items)
        n = len(items)
        n_train = int(0.70 * n)
        n_val = int(0.15 * n)
        if n >= 4:
            n_val = max(1, n_val)
            n_test = n - n_train - n_val
        else:
            n_test = 0

        train_set = items[:n_train]
        val_set = items[n_train:n_train + n_val]
        test_set = items[n_train + n_val:]

        for split_name, split_list in [("train", train_set), ("val", val_set), ("test", test_set)]:
            dst_dir = os.path.join(target_root, split_name, cat)
            os.makedirs(dst_dir, exist_ok=True)
            for fname, fpath, h in split_list:
                shutil.copy2(fpath, os.path.join(dst_dir, fname))
                split_summary[cat][split_name] += 1
                split_hashes[split_name].add(h)

    print("\n[DE-DUPLICATED DATASET SPLIT SUMMARY]")
    print(f"{'Category':<22} | {'Train':<8} | {'Val':<8} | {'Test':<8} | {'Total Clean':<12}")
    print("-" * 65)
    for cat in categories:
        tr = split_summary[cat]['train']
        va = split_summary[cat]['val']
        te = split_summary[cat]['test']
        tot = tr + va + te
        print(f"{cat:<22} | {tr:<8} | {va:<8} | {te:<8} | {tot:<12}")

    # Step 4: Strict Assertion — Zero Data Leakage Across Splits
    leak_tv = split_hashes["train"].intersection(split_hashes["val"])
    leak_tt = split_hashes["train"].intersection(split_hashes["test"])
    leak_vt = split_hashes["val"].intersection(split_hashes["test"])

    print(f"\n[LEAKAGE AUDIT VERIFICATION]")
    print(f"  * Train vs Val overlap:  {len(leak_tv)} (Target: 0)")
    print(f"  * Train vs Test overlap: {len(leak_tt)} (Target: 0)")
    print(f"  * Val vs Test overlap:   {len(leak_vt)} (Target: 0)")
    assert len(leak_tv) == 0 and len(leak_tt) == 0 and len(leak_vt) == 0, "FATAL: Data leakage detected across splits!"
    print("  -> ZERO LEAKAGE CONFIRMED: Train, Val, and Test splits are strictly disjoint. [PASSED]")
    print(f"\n[OK] Prepared clean dataset written to: {os.path.abspath(target_root)}")
    print("=" * 70)

if __name__ == "__main__":
    prepare_deduplicated_irdid_classification()
