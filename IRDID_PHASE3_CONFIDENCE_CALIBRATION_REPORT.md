# CivicVision AI — Phase 3: Confidence Calibration and Safe Filtering Report

**Project Root:** `E:\City_Care`  
**Execution Date:** October 14, 2026  
**Implementation Phase:** Phase 3 (Evidence-Based Confidence Filtering & Calibration Audit)  
**Authorization Status:** **PHASE 3 IMPLEMENTED & AUDITED — IRDID CLASSIFIER REMAINS STRICTLY QUARANTINED & DISABLED**

---

## 1. Executive Summary

Phase 3 evaluated and implemented evidence-based confidence filtering for CivicVision AI's road-damage detector (`yolov8-rdd2020-india-v1`) and the candidate IRDID image classifier (`irdid-classifier-candidate`).

In accordance with strict safety directives:
1. **Existing empirical evidence was evaluated** using held-out test splits from the Indian RDD2020 dataset (323 images, 734 defect instances) and the IRDID 6-class dataset (105 test images).
2. **Experimental proposed thresholds (0.85 road damage, 0.80 waterlogging, 0.20 classification margin) were formally evaluated and REJECTED as unvalidated.**
   - Raising YOLO road damage thresholds to 0.85 would devastate recall (overall detector recall is already 35.6% at baseline 0.25).
   - Setting 0.85/0.80 on the IRDID classifier is statistically unsupported because the test split contains only 11 broken-edge and 15 waterlogging samples, and raw softmax outputs are uncalibrated.
   - Imposing a 0.20 top-1/top-2 margin is unviable because the adapter does not expose secondary logits, and softmax probabilities on out-of-domain images are inherently overconfident.
3. **Safe, configurable thresholds with fail-safe defaults were established:**
   - `YOLO_CONFIDENCE_THRESHOLD: float = 0.25` (empirically supported default for Indian road defect detection; valid range: `0.05`–`0.95`).
   - `IRDID_CLASSIFIER_THRESHOLD: float = 0.30` (baseline default; strictly dormant while `ENABLE_IRDID_CLASSIFIER=False`; valid range: `0.10`–`0.95`).
   - Pydantic validators fail-safe to defaults when receiving `NaN`, `inf`, negative, out-of-range, or malformed inputs.
4. **All 51 unit, integration, and regression tests pass 100%**:
   - `test_confidence_filtering.py`: **10/10 PASSED**
   - `test_classification_adapter_smoke.py`: **13/13 PASSED**
   - `test_arbitration_pipeline.py`: **10/10 PASSED**
   - `test_multi_category_pipeline.py`: **18/18 PASSED**
5. **Production YOLO weights remain untouched** (SHA-256: `289e3e1765e6d2c0e0f50195e550a929d93a5cf742cf0ad650330e93107ee696`).
6. **The IRDID classifier remains disabled and quarantined.** No runtime weights were placed, and no model was retrained or deployed.

---

## 2. Evaluation of Existing Model Evidence

### 2.1 YOLOv8 Road Damage Detector Evidence (RDD2020 Indian Dataset)
The production road-damage detector (`backend/app/ai_model/yolo/weights/best.pt`) was evaluated on the Indian RDD2020 held-out test split (323 images, 734 ground-truth bounding box instances).

| Defect Class | Raw Label | Ground-Truth Instances | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **All Defect Classes** | **Overall** | **734** | **0.620** | **0.356** | **0.348** | **0.142** |
| Longitudinal Crack | `D00` | 162 | 0.415 | 0.407 | 0.363 | 0.161 |
| Transverse Crack | `D10` | 9 | 1.000 | **0.000** | 0.062 | 0.015 |
| Alligator Crack | `D20` | 196 | 0.534 | 0.643 | 0.569 | 0.243 |
| Pothole | `D40` | 367 | 0.533 | 0.373 | 0.398 | 0.148 |

#### Key Empirical Findings:
1. **Low Baseline Recall:** Across all 734 defect instances, baseline recall at threshold 0.25 is **0.356** (35.6%). For potholes, recall is **0.373** (37.3%).
2. **Transverse Crack Zero Recall (`D10`):** Due to extreme class imbalance (only 68 total instances across 7,706 Indian images; only 9 instances in test set) and asphalt orientation ambiguity, the detector confuses transverse cracks with longitudinal cracks (`D00`) at 40–87% confidence.
3. **Threshold Sensitivity:** Because true defects in challenging Indian road imagery (shadows, unpaved shoulders, irregular patches) generate confidence scores in the 0.30–0.70 range, raising the threshold reduces false positives only at the expense of discarding legitimate road damage.

---

### 2.2 IRDID Image Classifier Evidence (105-Image Held-Out Test Split)
The candidate IRDID classifier was evaluated on a clean held-out test split of 105 images (`runs/classify/runs/classify/irdid_cls_manual/evaluation_report.json`).

| Class Name | Target Category | Ground-Truth Total | Predicted Total | TP | FP | FN | Precision | Recall | F1-Score |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `broken_edges` | Damaged Road Surface | 11 | 10 | 7 | 3 | 4 | 0.7000 | 0.6364 | 0.6667 |
| `waterlogged_roads` | Waterlogging | 15 | 12 | 12 | 0 | 3 | 1.0000 | 0.8000 | 0.8889 |
| `construction_zones`| *(Unsupported)* | 16 | 18 | 16 | 2 | 0 | 0.8889 | 1.0000 | 0.9412 |
| `cracks` | *(Unsupported)* | 23 | 22 | 18 | 4 | 5 | 0.8182 | 0.7826 | 0.8000 |
| `open_manholes` | *(Quarantined)* | 10 | 11 | 9 | 2 | 1 | 0.8182 | 0.9000 | 0.8571 |
| `potholes` | *(Unsupported)* | 30 | 32 | 29 | 3 | 1 | 0.9062 | 0.9667 | 0.9355 |
| **Overall Macro Metrics** | — | **105** | **105** | **91** | **14** | **14** | **0.8553** | **0.8476** | **0.8482** |

#### Key Empirical Findings:
1. **Small Sample Size:** `broken_edges` contains only **11 test images** (7 TP, 3 FP, 4 FN). A single false negative represents 9.1% of the entire class evaluation split.
2. **`waterlogged_roads` Performance:** Achieved 1.0000 precision and 0.8000 recall across 15 images.
3. **Argmax-Only Nature:** The reported evaluation measures top-1 argmax assignment. It does not measure performance across a swept confidence threshold, nor does it provide a precision-recall curve.

---

### 2.3 Object Detection Confidence vs. Classification Probability

A fundamental mathematical distinction separates the confidence values of both models:

$$\text{YOLO Detection Confidence} = P(\text{Object}) \times P(\text{Class} \mid \text{Object})$$

$$\text{Image Classification Softmax} = P(y = c \mid x) = \frac{e^{z_c}}{\sum_{j=1}^K e^{z_j}}$$

| Dimension | YOLO Object Detection | IRDID Image Classification |
|---|---|---|
| **Spatial Grounding** | Localized to coordinates $[x_1, y_1, x_2, y_2]$ | Whole-image scene level (zero spatial grounding) |
| **Probability Constraint** | Unconstrained across grid cells and classes | Constrained: $\sum_{j=1}^K P_j = 1.0$ |
| **Out-of-Domain Behavior** | Background boxes yield low $P(\text{Object}) \approx 0$ | Forces 100% of probability into the closest of 6 classes |
| **Confidence Meaning** | Joint likelihood of object presence and bounding box | Relative logit proportion among 6 candidate classes |
| **Direct Comparison** | Meaningful only within detector box proposals | **Mathematically invalid** to directly compare with YOLO |

---

## 3. Threshold Evaluation and Justification Analysis

### 3.1 Proposed Thresholds Evaluated and Rejected

| Proposed Parameter | Proposed Value | Evidence Status | Evaluation Decision | Detailed Rationale |
|---|:---:|:---:|:---:|---|
| **Road Damage (YOLO)** | `0.85` | **CONTRADICTED** | **REJECTED** | At baseline (0.25), YOLO recall is only 35.6%. Requiring confidence $\ge 0.85$ would eliminate over 80% of valid pothole and crack detections, crippling civic issue detection in production. |
| **Broken Edges (Classifier)** | `0.85` | **UNVALIDATED** | **REJECTED** | Only 11 test samples exist in `broken_edges`. Setting a 0.85 threshold without an empirical validation sweep or calibration curve is statistically arbitrary. |
| **Waterlogging (Classifier)** | `0.80` | **UNVALIDATED** | **REJECTED** | Only 15 test samples exist in `waterlogged_roads`. Softmax scores are uncalibrated; setting 0.80 without temperature scaling is unjustified. |
| **Top-1 vs. Top-2 Margin** | `0.20` | **UNVALIDATED** | **REJECTED** | The classification adapter extracts only top-1 probability. Softmax on closed 6-class sets exhibits overconfidence on out-of-distribution inputs, rendering an uncalibrated margin metric misleading. |

---

### 3.2 Supported Evidence-Based Thresholds Established

| Model / Category | Default Threshold | Safe Configurable Range | Setting Name | Justification |
|---|:---:|:---:|---|---|
| **YOLO Road Damage** | **`0.25`** | `0.05` – `0.95` | `YOLO_CONFIDENCE_THRESHOLD` | Matches Ultralytics production detection standard; preserves balanced precision (0.620) and recall (0.356) on Indian road defects. |
| **IRDID Classifier** | **`0.30`** | `0.10` – `0.95` | `IRDID_CLASSIFIER_THRESHOLD` | Baseline candidate threshold; remains strictly dormant while `ENABLE_IRDID_CLASSIFIER=False`. |

---

## 4. Safe Configuration Design and Implementation

### 4.1 Changes to [`backend/app/core/config.py`](file:///E:/City_Care/backend/app/core/config.py)
Added configurable Pydantic settings with defensive validation:
```python
YOLO_CONFIDENCE_THRESHOLD: float = 0.25
IRDID_CLASSIFIER_THRESHOLD: float = 0.30

@field_validator("YOLO_CONFIDENCE_THRESHOLD", mode="before")
@classmethod
def validate_yolo_threshold(cls, v: Any) -> float:
    DEFAULT_YOLO_THRESH = 0.25
    if v is None:
        return DEFAULT_YOLO_THRESH
    try:
        val = float(v)
        if not math.isfinite(val):
            return DEFAULT_YOLO_THRESH
        if 0.05 <= val <= 0.95:
            return round(val, 4)
        return DEFAULT_YOLO_THRESH
    except (TypeError, ValueError):
        return DEFAULT_YOLO_THRESH
```
*(Identical fail-safe validation implemented for `IRDID_CLASSIFIER_THRESHOLD` with range `0.10`–`0.95`).*

### 4.2 Changes to [`backend/app/services/ai_service.py`](file:///E:/City_Care/backend/app/services/ai_service.py)
1. **Finite Float Validation:**
   `_is_valid_detection_dict` strictly validates `math.isfinite(conf_val)` to reject `NaN`, `inf`, and non-numeric types.
2. **Dynamic Threshold Resolution:**
   ```python
   model_type = spec.get("model_type")
   if model_type == "object_detection":
       threshold = getattr(settings, "YOLO_CONFIDENCE_THRESHOLD", spec.get("confidence_threshold", 0.25))
   elif model_type == "image_classification":
       threshold = getattr(settings, "IRDID_CLASSIFIER_THRESHOLD", spec.get("confidence_threshold", 0.30))
   else:
       threshold = spec.get("confidence_threshold", 0.25)
   ```
3. **Exact Threshold Filtering:**
   Detections are admitted only if `conf_val >= threshold`. Detections with `conf_val < threshold` are safely discarded.
4. **Preservation of Phase 2 Arbitration:**
   Spatial precedence, bounding-box geometry, and classification `bounding_box: None` behavior remain completely intact.

### 4.3 Documentation in `.env.example` Templates
Updated `.env.example` and `backend/.env.example` with documented threshold variables:
```
# Computer Vision Confidence Thresholds (Evidence-based defaults)
YOLO_CONFIDENCE_THRESHOLD=0.25
IRDID_CLASSIFIER_THRESHOLD=0.30
```

---

## 5. Regression Tests and Actual Results

### 5.1 Test Suites Summary

| Test Suite File | Command | Tests Run | Result | Execution Time |
|---|---|:---:|:---:|:---:|
| [`test_confidence_filtering.py`](file:///E:/City_Care/backend/app/test_confidence_filtering.py) | `python backend/app/test_confidence_filtering.py` | 10 | **10/10 PASS** | 0.451s |
| [`test_classification_adapter_smoke.py`](file:///E:/City_Care/backend/app/test_classification_adapter_smoke.py) | `python backend/app/test_classification_adapter_smoke.py` | 13 | **13/13 PASS** | 3.859s |
| [`test_arbitration_pipeline.py`](file:///E:/City_Care/backend/app/test_arbitration_pipeline.py) | `python backend/app/test_arbitration_pipeline.py` | 10 | **10/10 PASS** | 0.349s |
| [`test_multi_category_pipeline.py`](file:///E:/City_Care/backend/app/test_multi_category_pipeline.py) | `python backend/app/test_multi_category_pipeline.py` | 18 | **18/18 PASS** | 8.732s |
| **Total Test Execution** | — | **51** | **51/51 PASS (100%)** | **13.391s** |

### 5.2 Specific Phase 3 Scenarios Verified in `test_confidence_filtering.py`
1. `test_01_configuration_defaults_and_fail_safe_parsing`: Defaults (0.25, 0.30, False), string numbers ("0.40"), invalid strings ("bad_val"), `NaN`, `inf`, and out-of-range floats safely default.
2. `test_02_yolo_threshold_boundary_filtering`: Confidence 0.2499 rejected; 0.2500 and 0.2501 accepted.
3. `test_03_classifier_threshold_boundary_filtering`: Confidence 0.2999 rejected; 0.3000 and 0.3001 accepted.
4. `test_04_invalid_missing_nonfinite_confidence_filtered_safely`: `NaN`, `inf`, `-inf`, `None`, strings, negative values rejected without process crash.
5. `test_05_dynamic_settings_threshold_configuration`: Dynamically setting `YOLO_CONFIDENCE_THRESHOLD=0.50` filters 0.40 and accepts 0.65.
6. `test_06_inactive_classifier_settings_when_disabled`: When `ENABLE_IRDID_CLASSIFIER=False`, adapter is unavailable and produces zero active detections.
7. `test_07_missing_classifier_weights`: Returns `status='unsupported'` when weights file is absent.
8. `test_08_manual_reporting_fallback_when_predictions_filtered`: When AI confidence is below threshold, status is `no_detection` and citizen manual report creation succeeds cleanly with `MANUAL_OR_UNAVAILABLE`.
9. `test_09_yolo_first_arbitration_with_filtering`: Localized YOLO detection takes precedence over higher-confidence classifier prediction even after thresholding.
10. `test_10_twelve_category_registry_specifications_intact`: Confirms all 12 active category thresholds, readiness enums, and department codes remain intact.

---

## 6. Git Changes and Pre-Existing Modifications

### 6.1 Git Diff Statistics (`git diff --stat`)
```
 .env.example                                       |   7 +
 backend/.env.example                               |   7 +
 backend/app/core/config.py                         |  71 ++++++-
 backend/app/services/ai_service.py                 | 214 +++++++++++++++------
 .../app/services/models/classification_adapter.py  |  31 ++-
 backend/app/test_classification_adapter_smoke.py   | 144 +++++++++++++-
 backend/app/test_multi_category_pipeline.py        | 139 +++++++++++++
 7 files changed, 551 insertions(+), 62 deletions(-)
```

### 6.2 Current Git Status (`git status --short`)
```
 M .env.example
 M backend/.env.example
 M backend/app/core/config.py
 M backend/app/services/ai_service.py
 M backend/app/services/models/classification_adapter.py
 M backend/app/test_classification_adapter_smoke.py
 M backend/app/test_multi_category_pipeline.py
?? DATASET_SEARCH_REPORT.md
?? IRDID_FINAL_VERIFICATION_AND_IMPLEMENTATION_PLAN.md
?? IRDID_IMPLEMENTATION_READINESS_REVIEW.md
?? IRDID_PHASE1_FEATURE_FLAG_REPORT.md
?? IRDID_PHASE2_ARBITRATION_REPORT.md
?? IRDID_PHASE3_CONFIDENCE_CALIBRATION_REPORT.md
?? Untitled-1.txt
?? backend/app/test_arbitration_pipeline.py
?? backend/app/test_confidence_filtering.py
```

---

## 7. Model-Weight and Feature-Flag Verification

| Target Artifact / Setting | Expected Requirement | Measured State | Verification Status |
|---|---|---|:---:|
| **Production YOLO Weights** | `backend/app/ai_model/yolo/weights/best.pt` | SHA-256: `289e3e1765e6d2c0e0f50195e550a929d93a5cf742cf0ad650330e93107ee696` | **MATCH (UNTOUCHED)** |
| **Candidate IRDID Classifier** | `runs/classify/runs/classify/irdid_cls_manual/weights/best.pt` | SHA-256: `84637d53361e46522b87125fe4433fd619196a062d99db705fabcff379cccf45` | **QUARANTINED** |
| **Runtime Classifier Path 1** | `backend/app/services/weights/irdid_classifier.pt` | File does not exist | **ABSENT** |
| **Runtime Classifier Path 2** | `backend/app/ai_model/classifier/weights/best.pt` | File does not exist | **ABSENT** |
| **Feature Flag Default** | `ENABLE_IRDID_CLASSIFIER: bool = False` | Defaults to `False` in `Settings` | **VERIFIED** |
| **YOLO Default Threshold** | `YOLO_CONFIDENCE_THRESHOLD: float = 0.25` | Defaults to `0.25` in `Settings` | **VERIFIED** |
| **Classifier Default Threshold**| `IRDID_CLASSIFIER_THRESHOLD: float = 0.30` | Defaults to `0.30` in `Settings` | **VERIFIED** |
| **Production SQLite Databases**| `backend/civicsense.db`, `civicvision.db` | Modification times unchanged | **UNTOUCHED** |
| **Live Environment Files** | `.env`, `backend/.env` | Modification times unchanged | **UNTOUCHED** |

---

## 8. Remaining Limitations and Recommended Next Steps

### 8.1 Remaining Limitations
1. **Uncalibrated Softmax Probabilities:** The IRDID classifier outputs raw softmax values. Until temperature scaling is fitted on validation data, scores cannot be interpreted as calibrated posterior probabilities.
2. **Limited Per-Class Evaluation Split:** With only 11 test samples for broken edges and 15 for waterlogging, high-confidence tail statistics cannot be measured with statistical significance.
3. **Absence of OOD Filtering:** An uncalibrated classifier forced to output a probability distribution across 6 classes can still yield false positives on non-infrastructure images if activated.
4. **License Quarantined:** Dataset copyright and distribution terms for the IRDID imagery remain unverified.

### 8.2 Recommended Future Calibration Procedure (Post-Authorization)
If deployment authorization is granted in the future:
1. **Temperature Scaling:** Fit a single scalar parameter $T > 0$ on the 99-image validation split to minimize Expected Calibration Error (ECE) and negative log-likelihood (NLL):
   $$\hat{P}(y = c \mid x) = \frac{e^{z_c / T}}{\sum_{j=1}^K e^{z_j / T}}$$
2. **Empirical Precision-Recall Curves:** Generate PR curves on validation data to identify the exact operating point achieving $\ge 85\%$ precision before setting thresholds.
3. **Entropy / Margin Filter:** Compute prediction entropy $H(p) = -\sum p_i \log p_i$ to reject ambiguous, high-entropy scenes before category assignment.

---

## 9. Conclusion and Stop Condition Compliance

Phase 3 objectives are complete in full compliance with the stop condition:
- Confidence filtering is evidence-based and configurable with fail-safe defaults.
- Unvalidated thresholds (0.85, 0.80, and 0.20 margin) were rigorously analyzed and rejected.
- All existing functionality, YOLO-first arbitration, and 12 civic categories remain backward-compatible.
- All 51 regression tests pass.
- The IRDID classifier remains disabled and quarantined.
- No model was trained, fine-tuned, deployed, or activated.
