# Dataset Acquisition Final Checklist

This document details the precise, final manual workflow required to place and validate REAL data in the CivicVision AI repository before proceeding to Model Training.

**NO TRAINING SHOULD BEGIN BEFORE FINAL READINESS = READY.**

---

## A. RDD2020 India (YOLO Dataset)

**Official Source:** RDD2020 (India subset)

**What to download:**
- Download the official archive from [Mendeley](https://data.mendeley.com/datasets/5ty2wb6gvg/1) or via the official [RoadDamageDetector GitHub](https://github.com/sekilab/RoadDamageDetector).

**Expected Extraction Location & Structure:**
Extract the contents directly into `E:\City_Care\datasets\RDD2020\`. 
To avoid accidental duplicate nesting, verify your folder structure contains the India directory:

```text
E:\City_Care\datasets\RDD2020\
└── India\
    ├── train\
    │   ├── images\       <-- Your India .jpg images go here
    │   └── annotations\  <-- Your India .xml files go here
```
(Note: RDD2020 may extract into `India/Images/` and `India/Annotations/` depending on the archive.)

**Conversion Command:**
The RDD2020 dataset provides Pascal VOC XML annotations. You must run the conversion script before validation. This script will automatically convert the India subset into YOLO format and perform the train/val/test splits.
```bash
python backend/app/ml/convert_rdd_to_yolo.py --xml_dir datasets/RDD2020/India/annotations --img_dir datasets/RDD2020/India/images --out_dir datasets/RDD2020
```

**Validation Command:**
```bash
python backend/app/ml/validate_yolo_dataset.py --data datasets/RDD2020/data.yaml
```

---

## B. Priority Dataset (Tabular ML)

**Required Schema (13 Columns):**
1. `issue_count`: Integer
2. `damage_area`: Float
3. `detection_confidence`: Float
4. `severity`: Integer (1-4)
5. `road_age_years`: Float
6. `road_condition`: Float (0.0-1.0)
7. `traffic_volume`: Integer
8. `accident_history`: Integer
9. `nearby_school`: Binary (1/0)
10. `nearby_hospital`: Binary (1/0)
11. `drainage_condition`: Integer (1=Poor, 2=Fair, 3=Good)
12. `days_since_maintenance`: Integer
13. `priority_class`: Integer (1=Low, 2=Medium, 3=High, 4=Critical)

**Legitimate Source Requirements:**
No single open dataset provides this natively. You must geographically join data from legitimate open portals (e.g., San Diego Open Data, Open Data NI, OpenStreetMap) to combine 311 request locations with AADT traffic and POI mapping.

**Required Labeling Methodology (`priority_class`):**
The documentation defines the `priority_class` methodology as deriving from "Maintenance completion timeframes" (e.g., historical time-to-close metrics, where fixed < 48 hours = 4, fixed > 30 days = 1). If you lack historical completion data from the city, you cannot organically label this dataset and must explicitly define a strict, documented proxy methodology.

**Expected Extraction Location:**
Save your constructed CSV exactly here:
`E:\City_Care\datasets\priority\actual_dataset.csv`

**Validation Command:**
```bash
python backend/app/ml/validate_priority_dataset.py --data datasets/priority/actual_dataset.csv
```

---

## C. Final Readiness Sequence

1. **Place RDD2020 files** locally into `datasets/RDD2020/India/`.
2. **Place priority data** at `datasets/priority/actual_dataset.csv`.
3. **Convert XML → YOLO** if required (using `convert_rdd_to_yolo.py`).
4. **Validate YOLO** (`validate_yolo_dataset.py`).
5. **Validate Priority CSV** (`validate_priority_dataset.py`).
6. **Run Final Readiness Check**:
   ```bash
   python backend/app/ml/check_training_readiness.py
   ```
7. Only if the status is strictly `READY`, begin Phase 4 model training. NO TRAINING SHOULD BEGIN BEFORE FINAL READINESS = READY.
