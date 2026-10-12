# CivicVision AI — Dataset Manifest & Verification Catalog

This manifest records all Indian civic infrastructure datasets investigated, verified, and structured for CivicVision AI.

---

## 1. RDD2020 (India Split) — Road Damage Dataset
* **Dataset Name:** RDD2020 (Road Damage Dataset 2020 - India Subset)
* **Source Organization:** Sekilab / Global Road Damage Detection Challenge (GRDDC) / Figshare
* **Source URL:** https://github.com/sekilab/RoadDamageDetector / https://figshare.com/articles/dataset/RDD2020/13247078
* **Geographic Relevance:** 100% Indian road surface imagery (captured across Indian highways and urban streets via smartphone cameras mounted on vehicle dashboards).
* **License:** Creative Commons Attribution 4.0 International (CC BY 4.0)
* **Storage Location:** `datasets/RDD2020/`
  * Raw XMLs & Images: `datasets/RDD2020/India/` (7,706 images, 7,706 PASCAL VOC XMLs)
  * YOLO Formatted Split: `datasets/RDD2020/yolo/`
    * Train: 2,578 images with YOLO txt labels
    * Validation: 322 images with YOLO txt labels
    * Test: 323 images with YOLO txt labels
* **Annotation Format:** Bounding Boxes (PASCAL VOC XML & YOLO normalized xywh `.txt`)
* **Classes Covered:**
  * `D00`: Longitudinal Crack (311 instances in test/val)
  * `D10`: Transverse Crack (14 instances in test/val)
  * `D20`: Alligator Crack (384 instances in test/val)
  * `D40`: Pothole (673 instances in test/val)
* **Integrity Status:** 3,223 split images checked with zero corrupt files.
* **Training / Evaluation Readiness:** `READY_FOR_EVALUATION` & active in current YOLOv8 model (`best.pt`).

---

## 2. IRDID — Indian Road Damage & Infrastructure Dataset
* **Dataset Name:** Indian Road Damage & Infrastructure Dataset (IRDID)
* **Source Organization:** Curated Indian Research Collection
* **Source URL:** Local repository `Indian-Road-Damage-Infrastructure-Dataset`
* **Geographic Relevance:** 100% Indian urban and suburban streets across diverse lighting, monsoon wear, and road conditions.
* **License:** MIT License (per `LICENSE` in repository)
* **Storage Location:** `Indian-Road-Damage-Infrastructure-Dataset/`
* **Annotation Format:** Image-Level Classification (`annotations/labels.csv` with splits `splits/train.txt`, `splits/val.txt`, `splits/test.txt`)
* **Total Usable Images:** 1,049 verified non-corrupt images
* **Classes Covered:**
  1. `potholes`: 200 images (Depressions or cavities in road surface)
  2. `cracks`: 200 images (Linear fractures on pavement)
  3. `open_manholes`: 200 images (Exposed or partially covered utility manholes)
  4. `waterlogged_roads`: 200 images (Road sections submerged due to drainage failure)
  5. `broken_edges`: 147 images (Erosion or damage along road shoulders / damaged road surfaces)
  6. `construction_zones`: 102 images (Road sections under active repair/dug up)
* **Annotation Limitation:** Contains **image-level classification labels**, not bounding boxes or segmentation masks. To prevent fabricated predictions, bounding-box detection must not be claimed until bounding box or polygon annotations are manually annotated.
* **Training / Evaluation Readiness:** `IMAGE_LEVEL_LABELS_ONLY` (Ready for image classification / ResNet / MobileNet, or pending bounding-box annotation for YOLO).

---

## 3. Domestic Trash & Garbage Dataset (DataCluster Labs, India)
* **Dataset Name:** Domestic-Trash-Garbage-Dataset
* **Source Organization:** DataCluster Labs, India
* **Source URL:** https://github.com/datacluster-labs/Domestic-Trash-Garbage-Dataset
* **Geographic Relevance:** Crowdsourced across 2,000+ urban and rural locations across India (indoor and outdoor roadside waste).
* **License / Access Conditions:** Proprietary / Commercial with academic sample access via request (`sales@datacluster.ai`). Full automated download is restricted by authorization.
* **Classes Targeted:** Garbage Accumulation, Illegal Dumping, Overflowing Garbage Bins.
* **Training Readiness:** `DATASET_DOWNLOAD_BLOCKED` (Requires manual authorization/API token from DataCluster Labs).

---

## 4. SIH Vishudh Civic Waste Dataset
* **Dataset Name:** Project Vishudh Smart India Hackathon Dataset
* **Source Organization:** Team CTRL Alt Elite (SIH 2020)
* **Source URL:** https://github.com/0xamitdutta/SIH2020
* **Geographic Relevance:** Indian street waste and roadside garbage collection.
* **License:** Open Source MIT
* **Training Readiness:** `DATASET_NOT_FOUND` (Repository contains hackathon client/server code; large raw image dumps were hosted on expired cloud links).
