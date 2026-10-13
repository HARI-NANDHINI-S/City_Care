# CivicVision AI — Manual Model Training & Evaluation Guide
# Focus: Indian Infrastructure Defect Datasets & Multi-Model Architecture

This runbook provides exact, verified PowerShell commands to manually train, evaluate, and govern vision models for the CivicVision AI pipeline.

> **CRITICAL SAFETY DIRECTIVES:**
> 1. **No Automatic Training:** Do NOT train models automatically in background routines. Every training command documented here is intended exclusively for manual execution when compute resources are scheduled.
> 2. **Preserve Production Models:** Preserves the current working YOLOv8 road model: `backend/app/ai_model/yolo/weights/best.pt`.
> 3. **Preserve Runtime Weights:** NEVER copy candidate weights into `backend/app/services/weights/` or `backend/app/ai_model/` as part of training or evaluation. Candidate checkpoints remain strictly quarantined inside `runs/classify/irdid_cls_manual/`.
> 4. **No Synthetic Bounding Boxes:** Image-level classification outputs must NEVER be represented as bounding boxes or localized defect overlays.
> 5. **Exploratory Baseline Status:** The IRDID 6-class classifier is an **exploratory baseline experiment** with no established performance results until training and evaluation are officially scheduled and run.
> 6. **Deployment Requires Approval:** Passing preliminary metrics on a 105-image test set does NOT establish production readiness. Deployment requires explicit user approval following pre-deployment review.

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
│           ├── train\ {broken_edges, construction_zones, cracks, open_manholes, potholes, waterlogged_roads}
│           ├── val\   {broken_edges, construction_zones, cracks, open_manholes, potholes, waterlogged_roads}
│           └── test\  {broken_edges, construction_zones, cracks, open_manholes, potholes, waterlogged_roads}
├── training\indian_infrastructure\
│   ├── validate_dataset.py              # Automated integrity & leakage validator
│   ├── class_distribution_report.py     # Class instance & image count reporter
│   ├── prepare_irdid_classification.py  # Zero-leakage classification split generator
│   ├── evaluate_irdid_classification.py # Safe, read-only confusion matrix evaluation script
│   └── manual_training_guide.md         # This manual execution guide
├── backend\app\
│   ├── services\models\
│   │   ├── classification_adapter.py    # IRDID whole-image classification candidate adapter
│   │   └── registry.py                  # Model registry (quarantines candidate models)
│   └── test_classification_adapter_smoke.py # Isolated adapter smoke test
└── runs\classify\
    └── irdid_cls_manual\                # Isolated candidate training run output
        └── weights\ {best.pt, last.pt}  # Quarantined candidate checkpoints
```

---

## 2. Dataset Pre-Flight Validation

Before executing any manual training, run the integrity, leakage, and distribution verification tools:

```powershell
# Execute from project root: E:\City_Care
cd E:\City_Care

# 1. Verify RDD2020 bounding-box splits and IRDID zero data leakage
python training/indian_infrastructure/validate_dataset.py

# 2. Report class distributions across all splits
python training/indian_infrastructure/class_distribution_report.py

# 3. Pre-flight verification of the 6-class classification test split
python training/indian_infrastructure/evaluate_irdid_classification.py --verify-dataset-only
```

### Expected Pre-Flight Validation Output:
- **RDD2020:** 3,223 valid bounding-box images (zero missing labels, zero corrupt files).
- **IRDID Prepared Split:** 670 clean unique images partitioned into strictly disjoint splits with zero cross-split hash overlap:
  - `train`: 466 images across 6 classes
  - `val`: 99 images across 6 classes
  - `test`: 105 images across 6 classes (broken_edges: 11, construction_zones: 16, cracks: 23, open_manholes: 10, potholes: 30, waterlogged_roads: 15)

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

# Overwrite safeguard check
if (Test-Path "runs/detect/rdd2020_india_manual") {
    Write-Warning "Directory runs/detect/rdd2020_india_manual already exists! Use a unique name or archive existing run."
} else {
    yolo detect train data=datasets/RDD2020/data.yaml model=yolov8n.pt epochs=50 imgsz=640 batch=16 name=rdd2020_india_manual device=cpu
}
```
*(Replace `device=cpu` with `device=0` if using an NVIDIA GPU)*

---

### B. IRDID Image-Level Classification (Zero-Leakage Prepared Split)
Because IRDID contains image-level labels without bounding boxes, training must use a **classification model** (`yolov8n-cls.pt`) to avoid generating fabricated bounding boxes:

```powershell
cd E:\City_Care

# Overwrite safeguard check: Require explicit confirmation or unique run name
if (Test-Path "runs/classify/irdid_cls_manual") {
    Write-Warning "Directory 'runs/classify/irdid_cls_manual' already exists!"
    Write-Host "To prevent overwriting existing run artifacts, choose a unique run name (e.g. name=irdid_cls_manual_run02) or archive previous results."
} else {
    yolo classify train data=datasets/indian_infrastructure/irdid_prepared_classification model=yolov8n-cls.pt epochs=30 imgsz=224 batch=32 name=irdid_cls_manual device=cpu
}
```

#### Classification Scope & Structural Protocol:
- **Exploratory Baseline:** This model is an exploratory baseline experiment. It has no established baseline metrics until training and evaluation are manually run.
- **Whole-Image Scene Classification:** Predicts overall scene condition (Top-1 / Top-5 classification accuracy).
- **Zero Fabricated Bounding Boxes:** Does **not** produce bounding box coordinates or polygon masks. In the CivicVision pipeline, classification models populate category and severity metadata, but set `bounding_box: None`.
- **Quarantined Weights:** Checkpoints are stored strictly inside `runs/classify/irdid_cls_manual/weights/` and must NOT be moved to runtime directories during training.

---

### C. Manual Evaluation of Trained Models

#### 1. Object Detection Evaluation (RDD2020 Test Split)
```powershell
cd E:\City_Care
yolo detect val data=datasets/RDD2020/data.yaml model=runs/detect/rdd2020_india_manual/weights/best.pt split=test
```

#### 2. Candidate Classification Evaluation (IRDID Test Split — 105 images)
Execute the verified evaluation script:

```powershell
cd E:\City_Care
python training/indian_infrastructure/evaluate_irdid_classification.py --weights runs/classify/irdid_cls_manual/weights/best.pt --dataset datasets/indian_infrastructure/irdid_prepared_classification
```

#### Confusion Matrix Orientation & Correct Metrics Formulation:
In the installed Ultralytics classification engine (`ultralytics.utils.metrics.ConfusionMatrix.process_cls_preds`), predictions are accumulated via:
```python
for p, t in zip(preds, targets):
    self.matrix[p][t] += 1
```
The verified matrix orientation is: **`cm[predicted, true]`**.
- Row index $i$ corresponds to the predicted class. Total predictions for class $i$: $\sum_j cm[i, j]$.
- Column index $i$ corresponds to the true ground truth. Total ground truth for class $i$: $\sum_j cm[j, i]$.

From this verified orientation, metrics are calculated strictly as follows:
- **True Positives (TP):** $TP = cm[i, i]$
- **False Positives (FP):** $FP = cm[i, :].sum() - TP$ (Row sum minus TP)
- **False Negatives (FN):** $FN = cm[:, i].sum() - TP$ (Column sum minus TP)
- **Precision:** $P = \frac{TP}{TP + FP} = \frac{TP}{cm[i, :].sum()}$ when $TP + FP > 0$; defined as $0.0$ when no predictions were made for class $i$.
- **Recall:** $R = \frac{TP}{TP + FN} = \frac{TP}{cm[:, i].sum()}$ when $TP + FN > 0$; defined as $0.0$ when ground truth has zero samples for class $i$.
- **Overall Accuracy:** $\text{Accuracy} = \frac{\text{trace}(cm)}{cm.sum()}$ when $cm.sum() > 0$.

> **IMPORTANT:** Both overall accuracy and per-class metrics must be derived from the **exact same confusion matrix**. Do not mix metrics from disparate inference passes.

---

## 5. Approval-Gated Deployment Governance & Production Readiness Criteria

> [!CAUTION]
> **STRICT DIRECTIVE: DO NOT COPY CANDIDATE WEIGHTS TO PRODUCTION AUTOMATICALLY**
> Candidate weights (`runs/classify/irdid_cls_manual/weights/best.pt`) must NEVER be copied into runtime paths (`backend/app/services/weights/irdid_classifier.pt` or `backend/app/ai_model/classifier/weights/best.pt`) as an automatic post-training step.

### A. Exploratory Experiment Criteria vs. Municipal Deployment Criteria

The preliminary thresholds below represent **exploratory experiment criteria only** to assess whether training produced a viable baseline; they do **NOT** constitute municipal deployment acceptance criteria:

| Metric | Exploratory Experiment Threshold | Municipal Deployment Acceptance Status |
| :--- | :--- | :--- |
| Overall Top-1 Accuracy | $\ge 0.70$ on 105 test images | Insufficient alone. Requires real-world field validation. |
| Per-Class Recall (Broken Edges) | $\ge 0.65$ (11 test images) | Insufficient alone. Small sample size caveat applies. |
| Per-Class Recall (Waterlogging) | $\ge 0.65$ (15 test images) | Insufficient alone. High municipal liability category. |
| False Positives on High-Risk Classes | Explored & Documented | Zero tolerance for misclassifying hazardous defects. |

**Passing these preliminary thresholds on a 105-image test set does NOT establish production readiness.**

### B. Mandatory Pre-Deployment Review Checklist

Before requesting deployment approval, the engineering team must document and review:
1. **Full Confusion Matrix Analysis:** Verify that orientation $cm[\text{predicted}, \text{true}]$ matches ground-truth column totals.
2. **Per-Class Precision and Recall:** Scrutinize false positives and false negatives for high-liability categories (`open_manholes`, `waterlogged_roads`).
3. **Representative Misclassifications:** Inspect images where the model erred to identify visual blind spots (shadows, lighting, reflections).
4. **Dataset Suitability Assessment:** Acknowledge statistical limitations of a 105-image test split (e.g. 10 manhole images, 11 broken edge images).
5. **Adapter Contract Verification:** Run the isolated smoke test to ensure zero runtime regressions:
   ```powershell
   python backend/app/test_classification_adapter_smoke.py
   ```
6. **Rollback Plan:** Confirm that if candidate weights are disabled or removed, the backend gracefully degrades to `status: "unsupported"` and allows citizen manual reporting without system errors.

### C. Explicit Approval Gate

Production deployment requires a **separate, explicit written approval** from the system lead.

Only after receiving explicit approval:
1. Copy candidate weights to permanent storage:
   ```powershell
   # ONLY AFTER EXPLICIT APPROVAL:
   New-Item -ItemType Directory -Force -Path "backend/app/services/weights"
   Copy-Item "runs/classify/irdid_cls_manual/weights/best.pt" -Destination "backend/app/services/weights/irdid_classifier.pt"
   ```
2. Verify file integrity:
   ```powershell
   Get-FileHash -Algorithm SHA256 "backend/app/services/weights/irdid_classifier.pt"
   ```
3. Run full multi-category integration regression test suite:
   ```powershell
   python backend/app/test_multi_category_pipeline.py
   python backend/app/test_master_audit.py
   ```
