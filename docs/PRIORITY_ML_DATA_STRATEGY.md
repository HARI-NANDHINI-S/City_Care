# CivicVision AI — Priority ML Data Strategy & Dataset Research

## 1. Local Data Audit Summary

| Dataset Path / File | Type / Classification | Purpose | Can Train Priority ML? |
| :--- | :--- | :--- | :--- |
| `datasets/RDD2020/` | **REAL (CV Dataset)** | Object Detection (YOLOv8) | **NO** (Contains bounding box coordinates for D00, D10, D20, D40, not priority levels) |
| `datasets/RDD2022/` | **REAL (CV Manifest)** | Object Detection (YOLOv8) | **NO** (Contains computer vision defect images, no tabular priority data) |
| `datasets/priority/priority_dataset_template.csv` | **TEMPLATE / HEADER** | Schema definition | **NO** (Contains only 15 header/comment lines, 0 data rows) |
| `backend/app/ml/dataset.py` | **SYNTHETIC / MOCK** | Development testing | **NO** (Synthetic generator; disallowed for production ML per project guidelines) |

---

## 2. External Public Dataset Research

We evaluated multiple public datasets (focusing on India / Government Open Data as well as international municipal open data):

| DATASET | SOURCE | OFFICIAL URL | COUNTRY / REGION | RECORD COUNT | AVAILABLE FEATURES | TARGET / LABEL | LICENSE | GEOGRAPHIC GRANULARITY | CAN SUPPORT PRIORITY? | REASON |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **MoRTH India Road Accident & Surface Statistics** | data.gov.in / MoRTH | https://data.gov.in/catalog/road-accidents-india | India | ~5,000 | State/District, Road Type, Accidents, Surface Type | Aggregated Accident Counts | OGD India License | District / State level | **NO** | Macro-level annual statistics; lacks single-issue localized context and priority classes (1-4). |
| **San Diego 311 Get It Done Complaints** | San Diego Open Data | https://data.sandiego.gov/datasets/get-it-done-311/ | USA (San Diego, CA) | ~100,000+ | Request ID, Service Type, Open Date, Close Date, Lat, Long | Time-to-resolution | Public Domain | GPS Coordinates / District | **PARTIAL** | Contains issue types and resolution times, but lacks road age, traffic, accidents, school/hospital proximity. |
| **Open Data NI Road Defect & Maintenance Claims** | Open Data NI | https://www.opendatani.gov.uk | UK (Northern Ireland) | ~15,000 | Defect Category, Road Class, Repair Priority Code | Official Priority Code | OGL v3.0 | Road Network / Segment | **PARTIAL** | Contains official priority codes, but lacks image-based visual features (`damage_area`, `detection_confidence`). |

---

## 3. Severity vs. Priority Distinction

- **Severity:** The physical extent of structural damage (e.g., Pothole vs Crack, affected area in $m^2$). Calculated via computer vision (YOLO).
- **Priority:** The administrative urgency of repair, combining physical severity with contextual impact (traffic volume, school/hospital proximity, accident risk).

*Rule:* Physical severity cannot be arbitrarily transformed into an ML priority label without genuine ground-truth priority labels from municipal work orders.

---

## 4. Minimum Real Feature Schema Proposal

If a future municipal GIS dataset is linked, the minimum defensible feature schema is:

| FEATURE | SOURCE | TYPE | STATUS |
| :--- | :--- | :--- | :--- |
| `issue_count` | 311 Incident Count in 100m Radius | Integer | Requires GIS Spatial Index |
| `damage_area` | YOLO Detection Output ($m^2$) | Float | Requires Trained YOLO Weights |
| `detection_confidence` | YOLO Detection Confidence | Float | Requires Trained YOLO Weights |
| `severity` | Computer Vision Severity Level | Integer (1-4) | Real (In Database Schema) |
| `traffic_volume` | DOT Traffic Survey (AADT) | Integer | Requires Municipal Transport Data |
| `priority_class` | Municipal Work Order Priority | Integer (1-4) | Ground Truth Target |

Features such as `road_age_years`, `nearby_school`, `nearby_hospital`, `drainage_condition`, and `days_since_maintenance` are **omitted** from training unless a verified GIS spatial join connects them to the exact issue coordinates.

---

## 5. API Status & Honesty Guarantees

The CivicVision AI system enforces strict academic and technical honesty:
- `GET /api/v1/ml/models` returns `available: false` for Priority ML models.
- `GET /api/v1/ml/evaluation` returns `status: not_available`.
- `GET /api/v1/ml/predictions/{issue_id}` returns `status: not_available` with explicit reason.
- `GET /api/v1/ml/explanations/{issue_id}` returns `status: not_available` (SHAP disabled).

*No synthetic data, fake model weights, or heuristic fallbacks are permitted in the ML prediction path.*
