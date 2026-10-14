# CivicVision AI — Phase 2: YOLO-First Detection Arbitration Report

**Project Root:** `E:\City_Care`  
**Execution Date:** October 14, 2026  
**Implementation Phase:** Phase 2 (Safe Model-Result Arbitration & Spatial Precedence)  
**Authorization Status:** **PHASE 2 IMPLEMENTED & VERIFIED — IRDID CLASSIFIER REMAINS STRICTLY DISABLED & QUARANTINED**

---

## 1. Executive Summary

In Phase 2, CivicVision AI's computer vision pipeline was updated to implement **YOLO-First Detection Arbitration with Spatial Precedence**. 

Prior to this phase, the primary defect was selected using a naive confidence maximum (`max(valid_detections, key=lambda x: x["confidence"])`). Under dual-model conditions, an image-level classifier with higher nominal confidence (e.g., `Damaged Road Surface` at 0.95) would silently override fine-grained, localized YOLO object detections (e.g., `Pothole` at 0.65), destroying bounding-box coordinates, misattributing YOLO provenance, and distorting severity calculations.

With Phase 2 implementation:
1. **Localized YOLO detections take absolute precedence** over whole-image classification predictions when both are present for an image, regardless of confidence scores.
2. **All valid YOLO detections, bounding boxes, labels, and geometry are preserved** without loss or degradation.
3. **Classification predictions are considered for primary defect selection ONLY when zero valid localized detections exist** and the classification adapter is explicitly enabled and available.
4. **Classification predictions are never represented as localized detections**; they produce empty bounding-box lists (`bounding_boxes: []`), `bounding_box: None` in multi-defect details, and `defect_area_ratio: 0.0`.
5. **The IRDID classifier remains disabled by default** (`ENABLE_IRDID_CLASSIFIER=False`) and quarantined. No weights were copied, moved, or deployed.
6. **All 41 regression tests pass 100%**:
   - `test_arbitration_pipeline.py`: **10/10 PASSED**
   - `test_classification_adapter_smoke.py`: **13/13 PASSED**
   - `test_multi_category_pipeline.py`: **18/18 PASSED**

---

## 2. Files Changed and Technical Rationale

### 2.1 [`backend/app/services/ai_service.py`](file:///E:/City_Care/backend/app/services/ai_service.py)
- **Modifications:**
  1. Added `_is_valid_detection_dict(det: Any) -> bool`:
     Validates that raw detection outputs are valid dictionaries with non-empty string class names and numeric confidence scores within `[0.0, 1.0]`.
  2. Added `_is_valid_bounding_box(coords: Any, width: int, height: int) -> bool`:
     Validates 4-element coordinates `[x1, y1, x2, y2]`, confirming non-negative coordinates (`x1 >= 0`, `y1 >= 0`) and positive spatial extent (`x2 > x1`, `y2 > y1`).
  3. Defense-in-depth availability check:
     Ensures inactive or disabled adapters (`if not getattr(adapter, "is_available", True): continue`) are never invoked.
  4. Unsupported class filtering:
     Safely discards classes missing from `DEFECT_REGISTRY` before thresholding.
  5. Partitioning into localized vs. image-level detections:
     Differentiates categories based on `model_type == "image_classification"`. Categories designated for image classification strictly have `bounding_box: None`. Object detection categories require valid 4-element boxes; malformed boxes are safely rejected.
  6. **Spatial Precedence Arbitration Hierarchy:**
     ```python
     if localized_detections:
         best_detection = max(localized_detections, key=lambda x: x["confidence"])
         primary_category = best_detection["class"]
         primary_confidence = best_detection["confidence"]
     else:
         best_detection = max(classification_detections, key=lambda x: x["confidence"])
         primary_category = best_detection["class"]
         primary_confidence = best_detection["confidence"]
     ```
  7. Multi-defect and geometry construction:
     All localized detections populate `bounding_boxes` with complete geometry and normalized coordinates. Classification predictions populate `detected_defects` as secondary scene context with `bounding_box: None` and are never added to `bounding_boxes`.

### 2.2 [`backend/app/test_multi_category_pipeline.py`](file:///E:/City_Care/backend/app/test_multi_category_pipeline.py)
- **Modifications:**
  Added `test_18_yolo_first_spatial_arbitration_dual_model_coexistence` to the existing integration suite. Verifies that when a mock YOLO detector (`Pothole`, confidence `0.65`) and mock classifier (`Damaged Road Surface`, confidence `0.92`) are both active on the same image, `Pothole` remains the selected primary defect, bounding boxes are preserved, `is_real_yolo` is `True`, and issue creation persists the correct defect and coordinates.

### 2.3 [`backend/app/test_arbitration_pipeline.py`](file:///E:/City_Care/backend/app/test_arbitration_pipeline.py) *(New File)*
- **Modifications:**
  Created a dedicated, isolated regression test suite covering all 10 mandatory arbitration scenarios using mocks and ephemeral SQLite databases.

---

## 3. Arbitration Rules Implemented

| Rule | Requirement | Implementation in `ai_service.py` | Verification Status |
|---|---|---|:---:|
| **Rule 1** | Localized YOLO detections take precedence over classification predictions | If `localized_detections` is non-empty, `best_detection` is selected exclusively from localized detections. | **VERIFIED** |
| **Rule 2** | Preserve all valid YOLO detections and their bounding boxes | All detections in `localized_detections` are processed into `bounding_boxes` with full coordinates `[x, y, w, h]` and normalized boxes. | **VERIFIED** |
| **Rule 3** | Do not discard valid YOLO detections for higher classification confidence | Even when classifier confidence is 0.95 vs. YOLO confidence 0.65, YOLO is selected. | **VERIFIED** |
| **Rule 4** | Classification considered only when zero valid localized detections exist | The classifier can only provide the primary defect in the `else:` branch (`if not localized_detections`). | **VERIFIED** |
| **Rule 5** | Classification prediction must never be represented as a localized detection | Image classification detections are never added to `bounding_boxes`; their `bounding_box` attribute is strictly `None`. | **VERIFIED** |
| **Rule 6** | Preserve existing category mappings and unsupported-class filtering | Categories missing from `DEFECT_REGISTRY` or outside adapter `supported_categories` are safely filtered out. | **VERIFIED** |
| **Rule 7** | Do not invent bounding boxes, defect locations, area measurements, or severity | Classification yields `bounding_boxes: []`, `box_area: 0`, and `defect_area_ratio: 0.0`. No synthetic coordinates are created. | **VERIFIED** |
| **Rule 8** | Represent unavailable spatial info as `null` / established equivalent | Unavailable spatial coordinates are represented as `None` (JSON `null`) in `detected_defects`. | **VERIFIED** |
| **Rule 9** | Preserve manual citizen reporting as fallback | When automated inference returns `no_detection`, citizen submission via POST `/api/v1/issues` operates cleanly with `MANUAL_OR_UNAVAILABLE`. | **VERIFIED** |
| **Rule 10** | Keep existing API response structure backward-compatible | All 15 response dictionary keys and data types remain identical to the existing schema. | **VERIFIED** |

---

## 4. Regression Tests and Actual Results

All tests were executed in the project environment using Python 3.14.

### 4.1 Dedicated Arbitration Test Suite (`test_arbitration_pipeline.py`)
**Command:** `python backend/app/test_arbitration_pipeline.py`  
**Execution Time:** 0.365s  
**Result:** **10/10 PASSED (OK)**

Detailed scenario coverage:
1. `test_01_valid_yolo_detection_returned_when_no_classification`: **PASS** — Returns valid YOLO detection (`Pothole`, 0.75, bounding box intact, `is_real_yolo=True`).
2. `test_02_yolo_precedence_over_higher_confidence_classification`: **PASS** — YOLO `Pothole` (0.65) strictly prioritized over classifier `Damaged Road Surface` (0.95).
3. `test_03_multiple_valid_yolo_detections_preserved`: **PASS** — 3 distinct YOLO detections (`Pothole`, `Alligator Crack`, `Longitudinal Crack`) preserved with all 3 bounding boxes.
4. `test_04_classification_not_treated_as_bounding_box_detection`: **PASS** — Standalone classification (`Waterlogging`, 0.88) yields `bounding_boxes=[]`, `bounding_box=None`, `defect_area_ratio=0.0`.
5. `test_05_classification_ignored_when_feature_flag_disabled`: **PASS** — Checkpoint file on disk is ignored when `ENABLE_IRDID_CLASSIFIER=False`.
6. `test_06_classification_cannot_run_when_weights_missing`: **PASS** — Adapter returns `status='unsupported'` when weights file is absent.
7. `test_07_unsupported_classifier_classes_filtered`: **PASS** — Predictions for out-of-scope classes (`open_manholes`) return `raw_detections=[]`.
8. `test_08_manual_reporting_fallback_when_inference_unavailable`: **PASS** — Citizen manual issue creation succeeds with `ai_analysis_status='MANUAL_OR_UNAVAILABLE'`.
9. `test_09_empty_malformed_invalid_model_outputs_handled_safely`: **PASS** — Handles `None`, missing keys, string confidences, negative bounds, inverted boxes without crashing.
10. `test_10_twelve_category_registry_and_api_schema_unchanged`: **PASS** — Verifies all 12 active categories and exact response schema keys.

### 4.2 Smoke & Feature-Flag Regression Suite (`test_classification_adapter_smoke.py`)
**Command:** `python backend/app/test_classification_adapter_smoke.py`  
**Execution Time:** 3.591s  
**Result:** **13/13 PASSED (OK)**

### 4.3 Multi-Category Pipeline Integration Suite (`test_multi_category_pipeline.py`)
**Command:** `python backend/app/test_multi_category_pipeline.py`  
**Execution Time:** 9.892s  
**Result:** **18/18 PASSED (OK)** (including newly added `test_18`)

---

## 5. Git Changes and Pre-Existing Modifications

### 5.1 Pre-Existing State (Prior to Phase 2)
The working directory contained Phase 1 changes and previously verified report documents:
- Modified: `.env.example`, `backend/.env.example`, `backend/app/core/config.py`, `backend/app/services/models/classification_adapter.py`, `backend/app/test_classification_adapter_smoke.py`.
- Untracked: `DATASET_SEARCH_REPORT.md`, `IRDID_FINAL_VERIFICATION_AND_IMPLEMENTATION_PLAN.md`, `IRDID_IMPLEMENTATION_READINESS_REVIEW.md`, `IRDID_PHASE1_FEATURE_FLAG_REPORT.md`, `Untitled-1.txt`.

### 5.2 Git Changes Introduced in Phase 2
- Modified: `backend/app/services/ai_service.py` (arbitration implementation).
- Modified: `backend/app/test_multi_category_pipeline.py` (added `test_18`).
- Added: `backend/app/test_arbitration_pipeline.py` (10-scenario regression suite).
- Added: `IRDID_PHASE2_ARBITRATION_REPORT.md` (this report).

### 5.3 Git Status (`git status --short`)
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
?? Untitled-1.txt
?? backend/app/test_arbitration_pipeline.py
```

### 5.4 Git Diff Statistics (`git diff --stat`)
```
 .env.example                                       |   3 +
 backend/.env.example                               |   3 +
 backend/app/core/config.py                         |  24 ++-
 backend/app/services/ai_service.py                 | 187 +++++++++++++++------
 .../app/services/models/classification_adapter.py  |  31 +++-
 backend/app/test_classification_adapter_smoke.py   | 144 +++++++++++++++-
 backend/app/test_multi_category_pipeline.py        | 139 +++++++++++++++
 7 files changed, 471 insertions(+), 60 deletions(-)
```

---

## 6. Model-Weight and Feature-Flag Verification

| Target Artifact / Setting | Expected State | Measured / Actual Value | Verification Result |
|---|---|---|:---:|
| Production YOLO Weights | `backend/app/ai_model/yolo/weights/best.pt` | SHA-256: `289e3e1765e6d2c0e0f50195e550a929d93a5cf742cf0ad650330e93107ee696` | **UNTOUCHED & INTACT** |
| Candidate IRDID Classifier | `runs/classify/runs/classify/irdid_cls_manual/weights/best.pt` | SHA-256: `84637d53361e46522b87125fe4433fd619196a062d99db705fabcff379cccf45` | **STRICTLY QUARANTINED** |
| Runtime Weight Path 1 | `backend/app/services/weights/irdid_classifier.pt` | Does not exist | **ABSENT** |
| Runtime Weight Path 2 | `backend/app/ai_model/classifier/weights/best.pt` | Does not exist | **ABSENT** |
| Feature Flag Default | `ENABLE_IRDID_CLASSIFIER: bool = False` | Defaults to `False` in `Settings` | **VERIFIED** |
| Production Databases | `backend/civicsense.db`, `civicvision.db` | Unchanged mtime: Oct 12 / Oct 10 | **UNTOUCHED** |
| Live Environment Files | `.env`, `backend/.env` | Unchanged mtime: Oct 6 / Oct 10 | **UNTOUCHED** |

---

## 7. Remaining Limitations

While YOLO-first spatial arbitration is fully implemented and tested, the following limitations remain:
1. **Classifier Remains Quarantined & Inactive:** The IRDID classifier is intentionally disabled and cannot be activated without explicit administrative authorization and separate deployment approval.
2. **Confidence Calibration Not Performed:** Softmax probabilities from classification models remain uncalibrated. Temperature scaling or Platt scaling has not been applied in this phase.
3. **Out-of-Distribution (OOD) Filtering:** The pipeline does not yet compute prediction entropy or top-1 vs. top-2 probability margins to reject ambiguous scenes.
4. **Human Verification Workflow:** Disputed detections or category changes currently require manual officer review through existing `/verify-category` endpoints.
5. **No Automated Rollback Telemetry:** Real-time production telemetry and automated rollback triggers are reserved for future operations.

---

## 8. Conclusion and Stop Condition Compliance

Phase 2 objectives have been completed in full compliance with the stop condition:
- Valid localized YOLO detections cannot be overridden by whole-image classification predictions.
- Existing API contracts and schema structures remain 100% backward-compatible.
- All 41 unit, integration, and regression tests pass.
- The IRDID classifier remains disabled by default, quarantined, and absent from runtime locations.
- No production database, live `.env` file, frontend code, or model weight was altered.
