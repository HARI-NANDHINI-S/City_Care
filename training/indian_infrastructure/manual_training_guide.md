# CivicVision AI — Manual Model Training & Evaluation Guide
# Focus: Indian Infrastructure Defect Datasets & Multi-Model Architecture

This guide provides exact, verified PowerShell commands to manually train and evaluate vision models for the CivicVision AI pipeline.

> **CRITICAL DIRECTIVES:**
> 1. Do NOT train models automatically in background routines.
> 2. Every training and evaluation command documented here is intended for manual execution by the engineer when compute resources (GPU/CPU) are intentionally scheduled.
> 3. Preserves the current working YOLOv8 road model: `backend/app/ai_model/yolo/weights/best.pt`.
> 4. Image-level classification results must NEVER be represented as bounding boxes or localized defects.

---

## 1. Verified Directory Structure

```
E:\City_Care\
├── datasets\
│   ├── RDD2020\                         # Bounding-box detection dataset (India split)
│   │   ├── data.yaml                    # YOLO detection config (D00, D10, D20, D40)
│   │   └── yolo\
│   │       ├── images\ {train, val, test}
│   │       └── labels\ {train, val, test}
│   └── indian_infrastructure\
│       ├── DATASET_MANIFEST.md          # Multi-source dataset catalog
│       └── irdid_prepared_classification\ # Clean, deduplicated image classification split (Zero Leakage)
│           ├── train\ {broken_edges, waterlogged_roads, open_manholes, ...}
│           ├── val\   {broken_edges, waterlogged_roads, open_manholes, ...}
│           └── test\  {broken_edges, waterlogged_roads, open_manholes, ...}
└── training\indian_infrastructure\
    ├── validate_dataset.py              # Automated integrity & leakage validator
    ├── class_distribution_report.py     # Class instance & image count reporter
    ├── prepare_irdid_classification.py  # Zero-leakage classification split generator
    └── manual_training_guide.md         # This manual execution guide
```

---

## 2. Dataset Pre-Flight Validation

Before executing any manual training, run the integrity and leakage verification tools:

```powershell
cd E:\City_Care
python training/indian_infrastructure/validate_dataset.py
python training/indian_infrastructure/class_distribution_report.py
```

Expected Output:
- **RDD2020:** 3,223 valid bounding-box images (zero missing labels, zero corrupt files).
- **IRDID Prepared Split:** 670 clean unique images partitioned into strictly disjoint splits with zero cross-split leakage:
  - `train`: 466 images across 6 classes
  - `val`: 99 images across 6 classes
  - `test`: 105 images across 6 classes

---

## 3. Quantitative Evaluation of Existing Road-Detection Model

The existing road detection model (`backend/app/ai_model/yolo/weights/best.pt`) was evaluated against the held-out **Indian RDD2020 test split** (323 images, 734 ground-truth bounding box instances).

### Verification Command (PowerShell):
```powershell
cd E:\City_Care
python -c "from ultralytics import YOLO; model = YOLO('backend/app/ai_model/yolo/weights/best.pt'); metrics = model.val(data='datasets/RDD2020/data.yaml', split='test', device='cpu'); print('mAP50:', metrics.box.map50); print('mAP50-95:', metrics.box.map)"
```

### Measured Evaluation Metrics (Held-out Test Split):
| Class Name | Raw Label | Ground-Truth Instances | Precision (P) | Recall (R) | mAP@0.5 | mAP@0.5:0.95 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **All Defect Classes** | **Overall** | **734** | **0.620** | **0.356** | **0.348** | **0.142** |
| Longitudinal Crack | `D00` | 162 | 0.415 | 0.407 | 0.363 | 0.161 |
| Transverse Crack | `D10` | 9 | 1.000 | 0.000 | 0.062 | 0.015 |
| Alligator Crack | `D20` | 196 | 0.534 | 0.643 | **0.569** | **0.243** |
| Pothole | `D40` | 367 | 0.533 | 0.373 | **0.398** | **0.148** |

### Investigation of `D10` (Transverse Crack) Zero Recall:
1. **Acute Class Imbalance:** Across the entire 7,706-image Indian RDD2020 dataset, only 68 transverse crack instances exist (compared to 3,187 potholes and 2,021 alligator cracks). In the 323 test images, only 9 transverse crack annotations exist.
2. **Orientation Confusion:** Detailed inference inspection reveals that on the 9 test images containing transverse cracks, the model predicts `D00` (Longitudinal Crack) with 40–87% confidence or `D40` (Pothole). Because Indian road images contain multi-directional surface cracking with irregular asphalt borders, the detector frequently confuses transverse orientation with longitudinal cracks.
3. **No Class-ID Mismatch:** Model class definitions match `data.yaml` exactly: `0: D00, 1: D10, 2: D20, 3: D40`.

---

## 4. Manual Training Commands (PowerShell)

### A. Road Defect Detection (YOLOv8n — Bounding Box Detection)
For retraining or fine-tuning the road defect detector using RDD2020:

```powershell
cd E:\City_Care
yolo detect train data=datasets/RDD2020/data.yaml model=yolov8n.pt epochs=50 imgsz=640 batch=16 name=rdd2020_india_manual device=cpu
```
*(Replace `device=cpu` with `device=0` if using an NVIDIA GPU)*

---

### B. IRDID Image-Level Classification (Zero-Leakage Prepared Split)
Because IRDID contains image-level labels without bounding boxes, training must use a **classification model** (`yolov8n-cls.pt`) to avoid generating fabricated bounding boxes:

```powershell
cd E:\City_Care
yolo classify train data=datasets/indian_infrastructure/irdid_prepared_classification model=yolov8n-cls.pt epochs=30 imgsz=224 batch=32 name=irdid_cls_manual device=cpu
```

#### Classification Limitations & Protocol:
- Predicts overall image scene condition (Top-1 / Top-5 classification accuracy).
- Does **not** produce bounding box coordinates or polygon masks.
- In the CivicVision pipeline, classification models populate the defect category and severity, but do not draw bounding box overlays.

---

### C. Manual Evaluation of Trained Models

- **Object Detection Evaluation (mAP@0.5, mAP@0.5:0.95, Precision, Recall):**
  ```powershell
  cd E:\City_Care
  yolo detect val data=datasets/RDD2020/data.yaml model=runs/detect/rdd2020_india_manual/weights/best.pt split=test
  ```

- **Image Classification Evaluation (Top-1 Accuracy, Top-5 Accuracy, Confusion Matrix):**
  ```powershell
  cd E:\City_Care
  yolo classify val data=datasets/indian_infrastructure/irdid_prepared_classification model=runs/classify/irdid_cls_manual/weights/best.pt split=test
  ```

---

## 5. Model Registration & Integration Procedure

When a new model completes manual training:
1. Copy the resulting weights to a permanent location under `backend/app/ai_model/`:
   ```powershell
   New-Item -ItemType Directory -Force -Path "backend/app/ai_model/classifier/weights"
   Copy-Item "runs/classify/irdid_cls_manual/weights/best.pt" -Destination "backend/app/ai_model/classifier/weights/best.pt"
   ```
2. Verify its SHA-256 hash:
   ```powershell
   Get-FileHash -Algorithm SHA256 "backend/app/ai_model/classifier/weights/best.pt"
   ```
3. Create an adapter class inheriting from `BaseDefectModelAdapter` in `backend/app/services/models/`.
4. Register the adapter in `backend/app/services/models/registry.py`.
5. Run the regression test suite:
   ```powershell
   python backend/app/test_multi_category_pipeline.py
   python backend/app/test_master_audit.py
   ```
