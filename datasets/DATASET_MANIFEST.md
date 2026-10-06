# CivicVision Dataset Manifest

## 1. RDD2022 (Road Damage Dataset 2022)
*   **Dataset:** RDD2022
*   **Source:** Figshare / CRDDC'2022 GitHub / Kaggle
*   **URL:** [Figshare Link](https://figshare.com/articles/dataset/RDD2022/21431547) or [Kaggle](https://www.kaggle.com/datasets/datasetninja/road-damage-rdd2022)
*   **Purpose:** Core computer vision dataset to train YOLOv8 for detecting road surface defects.
*   **License:** Creative Commons (CC BY 4.0 or similar; check source)
*   **Format:** Varies (Pascal VOC XML or YOLO TXT)
*   **Classes:** D00 (Longitudinal Crack), D10 (Transverse Crack), D20 (Alligator Crack), D40 (Pothole)
*   **Number of samples:** ~47,000+ images globally (varies by subset)
*   **Local path:** `datasets/RDD2022/`
*   **Preparation required:** Extraction, and potentially XML to YOLO TXT conversion using `convert_rdd_to_yolo.py`.
*   **Validation status:** UNKNOWN (Requires manual download)
*   **Allowed for training:** YES
*   **Notes/limitations:** Excludes non-road-damage classes (like garbage or manholes). We only claim the 4 actual damage classes for the CV model.

## 2. Priority / Context Dataset
*   **Dataset:** Municipal Road Maintenance Dataset (e.g., San Diego Potholes or Open Data NI)
*   **Source:** Public Open Data Portals (e.g., [Open Data NI](https://www.opendatani.gov.uk) or [San Diego Open Data](https://data.sandiego.gov))
*   **URL:** Varies by chosen municipality.
*   **Purpose:** Train tabular ML models (Random Forest, Gradient Boosting, etc.) to predict maintenance priority.
*   **License:** Open Data / Public Domain
*   **Format:** CSV
*   **Classes:** Priority Levels (1=Low, 2=Medium, 3=High, 4=Critical)
*   **Number of samples:** UNKNOWN
*   **Local path:** `datasets/priority/`
*   **Preparation required:** Data cleaning, mapping column names to the CivicVision standard schema, filling missing values.
*   **Validation status:** UNKNOWN
*   **Allowed for training:** YES
*   **Notes/limitations:** If a complete real-world dataset is unavailable, an integration strategy combining multiple CSVs or using a single best-effort municipal CSV will be documented here. PROJECT-GENERATED proxy datasets for development must be strictly segregated.
