# CivicVision AI Datasets

## YOLO Dataset (Image Defect Detection)
**Dataset Name**: RDD2020 (India subset)
**Purpose**: Training YOLOv8 for detecting road defects from images.
**Supported Classes**:
- D00: Longitudinal Crack
- D10: Transverse Crack
- D20: Alligator Crack
- D40: Pothole

**Directory Structure**:
Place downloaded datasets in `datasets/RDD2020/`:
- `datasets/RDD2020/India/images/`
- `datasets/RDD2020/India/annotations/`
- After conversion:
- `datasets/RDD2020/images/` (train/val/test)
- `datasets/RDD2020/labels/` (train/val/test)
- `datasets/RDD2020/data.yaml`

**Preparation**:
1. Download RDD2020 dataset (India subset).
2. Place images and labels in the directory structure above.
3. Validate using: `python backend/app/ml/validate_yolo_dataset.py --data datasets/RDD2020/data.yaml`

---

## Priority Dataset (Contextual Prioritization)
**Dataset Name**: Municipal Road Maintenance Context
**Purpose**: Training tabular ML models (Random Forest, Gradient Boosting, Logistic Regression, Decision Trees) to predict maintenance priority based on image defects + context.

### Feature Definitions
The CSV must follow the exact schema defined in `datasets/priority/priority_dataset_template.csv`.

1. **issue_count**: Integer. Number of issues reported for a given road segment. Valid range: `[0, ∞)`.
2. **damage_area**: Float. Affected area of the defect in square meters or a normalized ratio. Valid range: `[0.0, ∞)`.
3. **detection_confidence**: Float. AI bounding box confidence. Valid range: `[0.0, 1.0]`.
4. **severity**: Integer. Base physical severity derived from defect type (e.g., Pothole=4, Long Crack=2). Valid range: `[1, 4]`.
5. **road_age_years**: Float. Years since the road was constructed or completely resurfaced.
6. **road_condition**: Float. Normalized metric representing overall wear. Valid range: `[0.0, 1.0]`.
7. **traffic_volume**: Integer. Average vehicles per day (AADT).
8. **accident_history**: Integer. Number of accidents reported on this segment in the past year.
9. **nearby_school**: Binary/Categorical. `1` if within school zone, `0` otherwise.
10. **nearby_hospital**: Binary/Categorical. `1` if within hospital/emergency route, `0` otherwise.
11. **drainage_condition**: Categorical. `1=Poor`, `2=Fair`, `3=Good`.
12. **days_since_maintenance**: Integer. Days since last minor/major repair.
13. **priority_class**: Integer (TARGET VARIABLE). Valid range: `[1, 4]` (1=Low, 2=Medium, 3=High, 4=Critical).

### Dataset Policies

*   **Real Municipal Records:** Features like `traffic_volume`, `accident_history`, and `days_since_maintenance` should be derived from real municipal Open Data (e.g., San Diego Open Data, Open Data NI).
*   **Target Labeling (priority_class):** The target must be labeled according to real maintenance prioritization logic. If a municipal labeling source is unavailable, a strict, deterministic labeling policy must be explicitly defined and documented *before* training.
*   **Data Splitting:** Use standard 80/20 train/test splits. Maintain class stratification since priority distributions are often highly imbalanced (many Low/Medium, few Critical).
*   **Invalid Data:** Nulls in critical fields (`priority_class`, `severity`) constitute invalid rows. Nulls in contextual fields should be imputed using median/mode before training.
*   **Target Leakage:** Ensure `priority_class` is not artificially derived directly and solely from `severity`, otherwise the model will just memorize the formula instead of learning complex interactions.

**Validation**:
Validate using: `python backend/app/ml/validate_priority_dataset.py --data datasets/priority/actual_dataset.csv`

---
**CRITICAL NOTE**: 
Do not mix PROJECT-GENERATED DATASET / SYNTHETIC DEVELOPMENT DATA with REAL EXTERNAL DATASET for production training. Use `--synthetic` flag on training scripts ONLY for development/testing, never for final model deployment.
