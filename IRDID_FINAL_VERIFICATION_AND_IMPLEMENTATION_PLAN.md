# CivicVision AI — IRDID Classifier Final Read-Only Verification and Implementation Plan

**Document Version:** 1.0.0  
**Date:** October 13, 2026  
**Auditor:** Antigravity AI Architecture & Safety Review Team  
**Project Root:** `E:\City_Care`  
**Candidate Checkpoint:** `runs\classify\runs\classify\irdid_cls_manual\weights\best.pt`  
**Operational Status:** **QUARANTINED — VERIFICATION & IMPLEMENTATION PLANNING ONLY (DEPLOYMENT STRICTLY UNAUTHORIZED)**

---

## 1. Executive Summary

This final forensic verification and implementation planning document completes the review cycle for the quarantined candidate Indian Road Damage and Infrastructure Dataset (IRDID) six-class image classifier.

### Key Verification Highlights
1. **Deliverable Documents Authenticated:**  
   Both documentation deliverables created in the previous task (`DATASET_SEARCH_REPORT.md` and `IRDID_IMPLEMENTATION_READINESS_REVIEW.md`) were physically inspected. They are bitwise identical copies (SHA-256: `9878f607...`, 28,152 bytes) containing the complete 10-section readiness review. Git history confirms that `DATASET_SEARCH_REPORT.md` never existed previously in version control and thus was not overwritten.
2. **Filename Discrepancy Resolved:**  
   No file named `IRDID_IMPLEMENTATION_READINESS_REVIEW_.md` (with an unexpected extra underscore or period) exists on disk. The exact filename is `IRDID_IMPLEMENTATION_READINESS_REVIEW.md`.
3. **Git Working-Tree Discrepancy Reconciled:**  
   The clean-tree discrepancy is fully resolved: the Git repository has **zero tracked modifications** (`git diff` is completely empty). The two created markdown reports reside as **untracked files** (`??`) because they are new documentation deliverables not yet added to `.gitignore` or committed to version control.
4. **Physical Quarantine & Production Baseline Maintained:**  
   The candidate weights remain quarantined at `runs\classify\runs\classify\irdid_cls_manual\weights\best.pt` (SHA-256: `84637d53...`). Runtime weight directories (`backend\app\services\weights\irdid_classifier.pt` and `backend\app\ai_model\classifier\weights\best.pt`) remain strictly empty. The production YOLOv8 checkpoint (`backend\app\ai_model\yolo\weights\best.pt`) matches its historical SHA-256 hash (`289e3e17...`) and has not been modified.
5. **Implementation Plan Established:**  
   A file-by-file, 12-point prioritized implementation plan is documented below. It provides the exact design, dependencies, failure modes, tests, and acceptance criteria required before implementation authorization.

**Final Verdict:** **VERIFIED — READY FOR IMPLEMENTATION APPROVAL**  
*(Deployment, code edits, weight copying, and runtime activation remain strictly prohibited until explicit stakeholder authorization is granted.)*

---

## 2. Documentation Deliverables Verification

A forensic inspection of the repository root was performed to verify all generated documentation artifacts:

| Document Filename | Full Physical Filesystem Path | File Size (Bytes) | Last Modified Timestamp | Cryptographic Hash (SHA-256) | Status |
|---|---|:---:|---|---|:---:|
| `DATASET_SEARCH_REPORT.md` | `E:\City_Care\DATASET_SEARCH_REPORT.md` | 28,152 | `2026-10-13T15:50:44` | `9878f6073665a15790222d344f10e6e30fe61508183d5a34e6fb9425fec574ae` | **VERIFIED** |
| `IRDID_IMPLEMENTATION_READINESS_REVIEW.md` | `E:\City_Care\IRDID_IMPLEMENTATION_READINESS_REVIEW.md` | 28,152 | `2026-10-13T15:51:34` | `9878f6073665a15790222d344f10e6e30fe61508183d5a34e6fb9425fec574ae` | **VERIFIED** |

### 2.1 Investigation of the Filename Query (`IRDID_IMPLEMENTATION_READINESS_REVIEW_.md`)
- A filesystem query (`Get-ChildItem -Path "E:\City_Care\IRDID*"`) confirmed that **no file named `IRDID_IMPLEMENTATION_READINESS_REVIEW_.md` exists on disk**.
- No file exists with a trailing underscore or an extra period before the extension.
- The single review document on disk is strictly named:
  ```
  E:\City_Care\IRDID_IMPLEMENTATION_READINESS_REVIEW.md
  ```

### 2.2 Content Analysis & Duplicate Status
- Both documents contain the exact 10-section implementation-readiness review requested in the previous task:
  1. Executive Summary
  2. Verified Current Architecture and Evidence
  3. Existing Behavior versus Proposed Changes
  4. Category Mapping and Model-Selection Rules
  5. Safeguards and Their Implementation Status
  6. Proposed Testing Matrix
  7. Risks, Dependencies, and Unresolved Questions
  8. Minimal Future Implementation Plan
  9. Deployment Approval Checklist
  10. Final Verdict
- Both files share the identical SHA-256 digest (`9878f607...`). They are bit-for-bit mirrors created to satisfy both primary (`DATASET_SEARCH_REPORT.md`) and secondary (`IRDID_IMPLEMENTATION_READINESS_REVIEW.md`) filename targets specified in task instructions.
- Neither file contains drafts, scratch notes, or unrelated content.

### 2.3 Prior Existence & Overwrite Verification
- A full-history Git audit was executed:
  ```powershell
  git log --all --full-history -- "DATASET_SEARCH_REPORT.md"
  ```
- Result: **Zero commits returned (empty)**.
- **Finding:** `DATASET_SEARCH_REPORT.md` had never been committed, tracked, or deleted in the Git history of `E:\City_Care`. It was created brand new in the preceding task. **No pre-existing file or prior audit document was overwritten or destroyed.**

---

## 3. Git Status & Working-Tree Reconciliation

Read-only Git verification commands were executed from the repository root `E:\City_Care`. Below are the verified observations.

### 3.1 Raw Git Command Outputs
1. **`git branch --show-current`**  
   Output: `main`
2. **`git rev-parse HEAD`**  
   Output: `2cd9e1531111bcc5ddbcab553e1420845060fe6b` (Commit message: "updation")
3. **`git status --short`**  
   Output:
   ```
   ?? DATASET_SEARCH_REPORT.md
   ?? IRDID_IMPLEMENTATION_READINESS_REVIEW.md
   ```
4. **`git status --short --untracked-files=all`**  
   Output:
   ```
   ?? DATASET_SEARCH_REPORT.md
   ?? IRDID_IMPLEMENTATION_READINESS_REVIEW.md
   ```
5. **`git diff` and `git diff --staged`**  
   Output: `[EMPTY — 0 lines]`
6. **`git check-ignore -v DATASET_SEARCH_REPORT.md IRDID_IMPLEMENTATION_READINESS_REVIEW.md`**  
   Exit Code: `1` (Standard Git exit code indicating that neither file is matched by `.gitignore`).

### 3.2 Root Cause of the Previous "Clean-Tree" Report Discrepancy
In the prior interaction:
1. `git status` was executed *prior* to document creation and truthfully reported `working tree clean`.
2. Following file generation, the textual summary stated *"Git working tree remains completely clean on branch main... with only the requested documentation deliverables created."*
3. This phrasing conflated **zero tracked modifications** with **working tree clean**. In strict Git terminology:
   - A tree is "clean" only when `git status` reports neither tracked modifications nor untracked files.
   - Because `DATASET_SEARCH_REPORT.md` and `IRDID_IMPLEMENTATION_READINESS_REVIEW.md` are uncommitted and unignored, they appear as untracked files (`??`).

### 3.3 Precise Working-Tree Classification

| Git State Category | Files Included | Verification Evidence |
|---|---|---|
| **Tracked Modifications** | **None (0 files)** | `git diff` and `git diff --staged` returned 0 modified lines. |
| **Untracked Files** | **2 files:**<br>• `DATASET_SEARCH_REPORT.md`<br>• `IRDID_IMPLEMENTATION_READINESS_REVIEW.md` | Displayed as `??` in `git status --short`. Unignored new deliverables. |
| **Ignored Files** | Build caches, virtual environments, raw datasets, databases, and local run folders:<br>• `.env`, `backend/.env`<br>• `civicsense.db`, `civicvision.db`, `backend/civicsense.db`<br>• `runs/`, `.venv/`, `frontend/node_modules/`, `weights/`<br>• `backend/app/ai_model/yolo/weights/` (parent dir) | Matched by `.gitignore` rules (displayed under `git status --ignored --short`). |
| **Tracked & Unchanged** | All repository source files, test suites, and documentation committed in `2cd9e153` and earlier commits. | Verified untouched. |

---

## 4. Confirmed Existing Architecture & Known Blockers

### 4.1 Checkpoint Isolation & Provenance (Direct Observations)
- **Candidate Classifier:**  
  Path: `runs\classify\runs\classify\irdid_cls_manual\weights\best.pt`  
  Size: `2,976,136 bytes` | SHA-256: `84637d53361e46522b87125fe4433fd619196a062d99db705fabcff379cccf45`  
  Internal PyTorch creation timestamp: `2026-10-13T15:23:31.092126+05:30` (Epoch 23 validation top-1 peak: 0.9091).  
  Physical Location: Within untracked/ignored directory `runs/`. **QUARANTINED.**
- **Production Runtime Paths (Verified Empty):**  
  `backend\app\services\weights\irdid_classifier.pt` $\longrightarrow$ **Does NOT exist** (`Test-Path = False`).  
  `backend\app\ai_model\classifier\weights\best.pt` $\longrightarrow$ **Does NOT exist** (`Test-Path = False`).
- **Production YOLO Checkpoint (Active & Untouched):**  
  Path: `backend\app\ai_model\yolo\weights\best.pt`  
  Size: `6,251,946 bytes` | SHA-256: `289e3e1765e6d2c0e0f50195e550a929d93a5cf742cf0ad650330e93107ee696`  
  Internal date: `2026-10-07T00:25:30.917114+05:30`. Unmodified since October 7, 2026.

### 4.2 Inspected Source Code Behavior
1. **Model Discovery Hazard ([`classification_adapter.py:L41-46`](file:///E:/City_Care/backend/app/services/models/classification_adapter.py#L41-L46)):**  
   `IRDIDClassificationAdapter.is_available` inspects solely `self._weights_path.exists()`. If candidate weights are copied to the runtime path, the adapter automatically activates on the next request.
2. **Arbitration Flaw ([`ai_service.py:L150-154`](file:///E:/City_Care/backend/app/services/ai_service.py#L150-L154)):**  
   `best_detection = max(valid_detections, key=lambda x: x["confidence"])`. If classification confidence exceeds YOLO detection confidence, coarse whole-image classification replaces the localized bounding-box detection as `primary_category`.
3. **Synthetic Bounding Box Suppression ([`classification_adapter.py:L84`](file:///E:/City_Care/backend/app/services/models/classification_adapter.py#L84)):**  
   The adapter sets `"bounding_box": None`. In `ai_service.py:L107-146`, non-spatial detections do not populate `bounding_boxes` (remains `[]`) and write `bounding_box: None` to `detected_defects`.
4. **Category Isolation ([`defect_registry.py:L220-260`](file:///E:/City_Care/backend/app/core/defect_registry.py#L220-L260)):**  
   `Damaged Drainage Covers` is registered under `DefectDomain.DRAINAGE` (`DEPT_DRAIN`), while `Open Manhole` is registered under `DefectDomain.UTILITY` (`DEPT_SEW`, `is_active_scope: False`). They are physically and administratively separated.
5. **Manual Reporting Fallback ([`issues.py:L88-113`](file:///E:/City_Care/backend/app/api/v1/endpoints/issues.py#L88-L113)):**  
   If AI is unavailable or no defects are detected, issue creation defaults to `status = IssueStatus.REPORTED`, `ai_analysis_status = "MANUAL_OR_UNAVAILABLE"`, preserving manual citizen reports.

### 4.3 Confirmed Deployment Blockers
- **Blocker 1 (Software):** Absence of an explicit feature flag to prevent accidental activation.
- **Blocker 2 (Software):** Absence of a spatial precedence rule in `ai_service.py` to prevent classifier from eclipsing YOLO.
- **Blocker 3 (Performance):** Low recall (**63.64%**) on `broken_edges` in held-out test data (4 out of 11 damaged road edges missed).
- **Blocker 4 (Legal):** Unverified commercial and municipal redistributable licensing terms for the IRDID dataset.

---

## 5. Prioritized, File-by-File Future Implementation Plan

The following plan covers the 12 required areas in strict priority order. **No item is to be implemented without prior approval.**

```
Priority 1: Feature Flag & Config Gate (config.py, .env.example)
      │
Priority 2: Weight Discovery Gating (classification_adapter.py)
      │
Priority 3: Spatial Precedence Arbitration (ai_service.py)
      │
Priority 4: Strict Category Mapping Allowlist (classification_adapter.py)
      │
Priority 5: Unsupported Class Rejection (classification_adapter.py)
      │
Priority 6: Bounding Box None Invariant (classification_adapter.py, ai_service.py)
      │
Priority 7: Human Verification Flagging (issues.py, defect_registry.py)
      │
Priority 8: Manual Reporting Fallback Preservation (ai_service.py, issues.py)
      │
Priority 9: Configurable Confidence Handling (defect_registry.py, classification_adapter.py)
      │
Priority 10: Dataset Licensing Documentation (datasets/DATASET_MANIFEST.md)
      │
Priority 11: Comprehensive Test Suites (test_classification_adapter_smoke.py, test_multi_category_pipeline.py)
      │
Priority 12: Operational Monitoring & Rollback (ai_service.py, logging config)
```

---

### Area 1: Add Explicit Classifier Feature Flag
- **Files Affected:**  
  - [`backend/app/core/config.py`](file:///E:/City_Care/backend/app/core/config.py)
  - `backend/.env.example`
- **Purpose & Expected Behavior:**  
  Add `ENABLE_IRDID_CLASSIFIER: bool = False` to application `Settings`. By default, the classifier is disabled at startup even if valid weights are present on disk.
- **Dependencies:** None.
- **Required Tests:**  
  Unit test asserting `settings.ENABLE_IRDID_CLASSIFIER` defaults to `False`.
- **Risks & Acceptance Criteria:**  
  *Risk:* Environment variable typo causes unexpected default.  
  *Acceptance Criteria:* Application starts cleanly with `ENABLE_IRDID_CLASSIFIER=False`; flag is readable via `settings`.
- **Approval Required Before Implementation:** **YES**

---

### Area 2: Prevent Classifier Activation Solely by File Existence
- **Files Affected:**  
  - [`backend/app/services/models/classification_adapter.py`](file:///E:/City_Care/backend/app/services/models/classification_adapter.py)
- **Purpose & Expected Behavior:**  
  Modify `IRDIDClassificationAdapter.is_available` to require **both** conditions:
  1. `settings.ENABLE_IRDID_CLASSIFIER is True`
  2. `self._weights_path.exists()`  
  If the flag is `False`, `is_available` returns `False` and `_lazy_load()` is never called.
- **Dependencies:** Area 1 (`config.py`).
- **Required Tests:**  
  Test adapter instantiation with weights present but flag set to `False`; assert `adapter.is_available == False` and `adapter.infer()` returns `status="unsupported"`.
- **Risks & Acceptance Criteria:**  
  *Risk:* Accidental weight copying activates model in staging/production.  
  *Acceptance Criteria:* Having the `.pt` file on disk does not activate the adapter unless the environment flag is explicitly `True`.
- **Approval Required Before Implementation:** **YES**

---

### Area 3: Preserve Existing YOLO Precedence Over Scene Classification
- **Files Affected:**  
  - [`backend/app/services/ai_service.py`](file:///E:/City_Care/backend/app/services/ai_service.py)
- **Purpose & Expected Behavior:**  
  Replace raw `max(valid_detections, key=lambda x: x["confidence"])` at `L150-154` with a multi-model arbitration hierarchy:
  - If any valid localized detection (`bounding_box is not None` from YOLO) exists, `primary_category` **must** be selected from YOLO detections.
  - Scene-level classification (`Damaged Road Surface` or `Waterlogging`) can become `primary_category` **only if zero valid YOLO detections exist**.
  - Classification results are always recorded in `detected_defects` for secondary context.
- **Dependencies:** None.
- **Required Tests:**  
  Integration test with synthetic dual-model output (YOLO confidence 0.65 vs. Classifier confidence 0.88); assert primary defect is YOLO's class and bounding boxes are preserved.
- **Risks & Acceptance Criteria:**  
  *Risk:* Regression where pothole coordinates are discarded in favor of whole-image label.  
  *Acceptance Criteria:* YOLO detections are never replaced by image-level classification.
- **Approval Required Before Implementation:** **YES**

---

### Area 4: Restrict Classifier Outputs to `Damaged Road Surface` and `Waterlogging`
- **Files Affected:**  
  - [`backend/app/services/models/classification_adapter.py`](file:///E:/City_Care/backend/app/services/models/classification_adapter.py)
- **Purpose & Expected Behavior:**  
  Maintain an immutable allowlist dictionary in `IRDIDClassificationAdapter`:
  ```python
  CLASS_MAPPING = {
      "broken_edges": "Damaged Road Surface",
      "waterlogged_roads": "Waterlogging"
  }
  SUPPORTED_CATEGORIES = ["Damaged Road Surface", "Waterlogging"]
  ```
  Only these two categories can be returned in `raw_detections`.
- **Dependencies:** None.
- **Required Tests:**  
  Unit tests validating that `broken_edges` maps to `Damaged Road Surface` and `waterlogged_roads` maps to `Waterlogging`.
- **Risks & Acceptance Criteria:**  
  *Risk:* Inadvertent mapping to unapproved municipal categories.  
  *Acceptance Criteria:* Adapter outputs only the two approved category names.
- **Approval Required Before Implementation:** **YES**

---

### Area 5: Reject Unsupported Classes & Prevent False Category Mappings
- **Files Affected:**  
  - [`backend/app/services/models/classification_adapter.py`](file:///E:/City_Care/backend/app/services/models/classification_adapter.py)
- **Purpose & Expected Behavior:**  
  Explicitly filter candidate classes `cracks`, `potholes`, `construction_zones`, and `open_manholes`:
  - When the model predicts any of these four classes, the adapter returns `raw_detections: []` and `status: "success"`.
  - Specifically prevent `open_manholes` from mapping to `Damaged Drainage Covers`.
- **Dependencies:** Area 4.
- **Required Tests:**  
  Unit test feeding all four excluded classes through mock model; assert `raw_detections == []` for each.
- **Risks & Acceptance Criteria:**  
  *Risk:* Cross-department ticket misrouting (Sewerage vs. Stormwater Drainage).  
  *Acceptance Criteria:* Zero detections generated for any excluded class.
- **Approval Required Before Implementation:** **YES**

---

### Area 6: Preserve `bounding_box: None` and Empty Bounding-Box Collections
- **Files Affected:**  
  - [`backend/app/services/models/classification_adapter.py`](file:///E:/City_Care/backend/app/services/models/classification_adapter.py)
  - [`backend/app/services/ai_service.py`](file:///E:/City_Care/backend/app/services/ai_service.py)
- **Purpose & Expected Behavior:**  
  Ensure that whole-image classification never fabricates coordinates:
  - Adapter returns `detection["bounding_box"] = None`.
  - `ai_service.py` leaves `bounding_boxes: []`, `defect_area_ratio: 0.0`, and skips OpenCV rectangle drawing.
  - `IssueImage.bounding_box_json` persists as `"[]"`.
- **Dependencies:** None.
- **Required Tests:**  
  Assertion checking that no bounding box coordinates exist in API response or database record for classification-only submissions.
- **Risks & Acceptance Criteria:**  
  *Risk:* Fabricated full-image bounding boxes corrupting map overlay and spatial density clustering.  
  *Acceptance Criteria:* `bounding_boxes` is strictly empty list; `bounding_box` in defect item is strictly `None`.
- **Approval Required Before Implementation:** **YES**

---

### Area 7: Require Human Verification for Damaged Road Surface Predictions
- **Files Affected:**  
  - [`backend/app/api/v1/endpoints/issues.py`](file:///E:/City_Care/backend/app/api/v1/endpoints/issues.py)
  - [`backend/app/core/defect_registry.py`](file:///E:/City_Care/backend/app/core/defect_registry.py)
- **Purpose & Expected Behavior:**  
  Given the verified 63.64% recall (36.36% false negative rate) and potential visual ambiguity with asphalt fatigue:
  - Add `requires_human_verification: bool = True` to `Damaged Road Surface` defect registry metadata.
  - When an issue is created via `Damaged Road Surface` classification, initialize its status to `IssueStatus.UNDER_REVIEW` (or flagged for triage) rather than automated dispatch.
- **Dependencies:** Area 4.
- **Required Tests:**  
  Endpoint test verifying that issue creation with `Damaged Road Surface` sets review flag and assigns triage state.
- **Risks & Acceptance Criteria:**  
  *Risk:* Unverified reports triggering erroneous contractor work orders.  
  *Acceptance Criteria:* Automated dispatch blocked until municipal operator confirms photo.
- **Approval Required Before Implementation:** **YES**

---

### Area 8: Preserve Manual-Reporting Fallback
- **Files Affected:**  
  - [`backend/app/services/ai_service.py`](file:///E:/City_Care/backend/app/services/ai_service.py)
  - [`backend/app/api/v1/endpoints/issues.py`](file:///E:/City_Care/backend/app/api/v1/endpoints/issues.py)
- **Purpose & Expected Behavior:**  
  Guarantee that when the classifier is disabled (`ENABLE_IRDID_CLASSIFIER=False`), missing weights, or experiencing exceptions:
  - `/analyze-image` returns graceful `vision_unavailable` or `no_detection`.
  - Citizens can select category manually and submit reports with `status = IssueStatus.REPORTED` and `ai_analysis_status = "MANUAL_OR_UNAVAILABLE"`.
- **Dependencies:** None.
- **Required Tests:**  
  End-to-end endpoint regression test simulating corrupt weights file; assert citizen can submit manual report successfully.
- **Risks & Acceptance Criteria:**  
  *Risk:* ML component failure cascading into citizen report submission downtime.  
  *Acceptance Criteria:* Manual reporting succeeds with 200 OK regardless of model availability.
- **Approval Required Before Implementation:** **YES**

---

### Area 9: Define Configurable Confidence Handling
- **Files Affected:**  
  - [`backend/app/core/defect_registry.py`](file:///E:/City_Care/backend/app/core/defect_registry.py)
  - [`backend/app/services/models/classification_adapter.py`](file:///E:/City_Care/backend/app/services/models/classification_adapter.py)
- **Purpose & Expected Behavior:**  
  - Update `confidence_threshold` in `defect_registry.py` for `Damaged Road Surface` (propose `0.85`) and `Waterlogging` (propose `0.80`).
  - Add top-1 vs. top-2 probability margin check ($\text{top1} - \text{top2} \ge 0.20$) in the adapter to reject ambiguous images.
  - Add docstring/metadata clearly stating that softmax scores represent raw model confidences, **not calibrated posterior probabilities**.
- **Dependencies:** None.
- **Required Tests:**  
  Unit test providing ambiguous probabilities `[0.48, 0.44, ...]`; assert adapter rejects classification due to insufficient margin.
- **Risks & Acceptance Criteria:**  
  *Risk:* Misrepresenting heuristic scores as statistical probabilities.  
  *Acceptance Criteria:* Margin filter rejects ambiguous predictions; scores documented as uncalibrated.
- **Approval Required Before Implementation:** **YES**

---

### Area 10: Document Dataset Licensing & Usage Permissions
- **Files Affected:**  
  - `datasets/DATASET_MANIFEST.md`
  - Documentation / legal repository log
- **Purpose & Expected Behavior:**  
  - Audit source terms for the Indian Road Damage and Infrastructure Dataset (IRDID).
  - Record license type (e.g., CC BY 4.0, academic-only, commercial allowed) and municipal operational compatibility.
  - Maintain a formal license clearance certificate before any production redistribution.
- **Dependencies:** External legal review.
- **Required Tests:** Non-code administrative audit check.
- **Risks & Acceptance Criteria:**  
  *Risk:* Legal liability from deploying academically restricted dataset weights in municipal production.  
  *Acceptance Criteria:* Formal license record approved and committed.
- **Approval Required Before Implementation:** **YES**

---

### Area 11: Comprehensive Test Suites Using Ephemeral Databases
- **Files Affected:**  
  - [`backend/app/test_classification_adapter_smoke.py`](file:///E:/City_Care/backend/app/test_classification_adapter_smoke.py)
  - [`backend/app/test_multi_category_pipeline.py`](file:///E:/City_Care/backend/app/test_multi_category_pipeline.py)
  - `backend/app/test_classifier_integration.py` (New test file)
- **Purpose & Expected Behavior:**  
  Implement automated test coverage without mutating production databases:
  - Use `sqlite:///:memory:` or ephemeral temporary test databases (`tempfile.mkdtemp`).
  - Unit tests: Feature flag toggling, mapping, margin checks, exception handling.
  - Integration tests: Dual-model arbitration, regression against YOLO detector, issue persistence.
  - Assert that `civicsense.db` is never opened or altered.
- **Dependencies:** Areas 1–9.
- **Required Tests:**  
  Test suite execution verifying 100% pass rate across all new and existing test fixtures.
- **Risks & Acceptance Criteria:**  
  *Risk:* Accidental write to live `civicsense.db` during test runs.  
  *Acceptance Criteria:* Test suite executes in isolated environment; production DB timestamps unchanged.
- **Approval Required Before Implementation:** **YES**

---

### Area 12: Define Monitoring, Failure Handling, and Rollback Procedure
- **Files Affected:**  
  - [`backend/app/services/ai_service.py`](file:///E:/City_Care/backend/app/services/ai_service.py)
  - Application logging configuration
- **Purpose & Expected Behavior:**  
  - Structured telemetry logging: Log `timestamp`, `model_id`, `raw_class`, `confidence`, and `mapped_category` on each classification invocation without citizen PII.
  - Failure handling: Inference exceptions log error stack trace and return `status="error"` without halting application.
  - Operational rollback procedure: Setting `ENABLE_IRDID_CLASSIFIER=False` in `.env` immediately deactivates the classifier on application restart ($< 30\text{s}$ procedure).
- **Dependencies:** Area 1.
- **Required Tests:**  
  Rollback drill in staging: toggle environment flag to `False` and verify classifier stops executing.
- **Risks & Acceptance Criteria:**  
  *Risk:* Unobserved model drift or high false-alarm rates in production.  
  *Acceptance Criteria:* Telemetry captures model activity; toggle reliably disables model.
- **Approval Required Before Implementation:** **YES**

---

## 6. Proposed Testing Matrix & Measurable Acceptance Criteria

| Test ID | Test Category | Target Component | Test Scenario & Assertion | Acceptance Criteria |
|:---:|---|---|---|---|
| **TM-01** | **Unit** | `classification_adapter.py` | Feature flag `ENABLE_IRDID_CLASSIFIER=False` with weights present. | `is_available == False`, `infer()` returns `status="unsupported"`. |
| **TM-02** | **Unit** | `classification_adapter.py` | Feature flag `ENABLE_IRDID_CLASSIFIER=True` with valid mock weights. | `is_available == True`, model loads lazily on first infer call. |
| **TM-03** | **Unit** | `classification_adapter.py` | Model predicts `broken_edges` (conf 0.90). | Returns `Damaged Road Surface`, `bounding_box: None`. |
| **TM-04** | **Unit** | `classification_adapter.py` | Model predicts `waterlogged_roads` (conf 0.88). | Returns `Waterlogging`, `bounding_box: None`. |
| **TM-05** | **Unit** | `classification_adapter.py` | Model predicts `cracks`, `potholes`, `construction_zones`, `open_manholes`. | Returns `raw_detections: []` for all 4 classes. |
| **TM-06** | **Unit** | `classification_adapter.py` | Model predicts ambiguous probabilities ($\text{top1} - \text{top2} < 0.20$). | Returns `raw_detections: []` (margin abstention). |
| **TM-07** | **Integration** | `ai_service.py` | Dual inference: YOLO detects `Pothole` (0.65), Classifier predicts `Damaged Road Surface` (0.85). | Primary category is `Pothole`; bounding boxes preserved. |
| **TM-08** | **Integration** | `ai_service.py` | Single inference: Zero YOLO detections, Classifier predicts `Waterlogging` (0.85). | Primary category is `Waterlogging`; `bounding_boxes: []`. |
| **TM-09** | **Integration** | `issues.py` | Issue creation with `Damaged Road Surface`. | `IssueImage.bounding_box_json == "[]"`, review flag set to `True`. |
| **TM-10** | **Regression** | `ai_service.py` | Run 50 standard test images with classifier disabled. | YOLO bounding boxes match baseline hash within $\epsilon < 10^{-6}$. |
| **TM-11** | **Regression** | `issues.py` | Missing classifier weights fallback. | Citizen report persists with `status=REPORTED`, `MANUAL_OR_UNAVAILABLE`. |
| **TM-12** | **Isolation** | Test Runner | Execute entire test suite. | `civicsense.db` modification timestamp strictly unchanged. |

---

## 7. Dataset Licensing and Model-Performance Limitations

### 7.1 Dataset Licensing Limitation
- **Status:** **NOT VERIFIED**.
- The prepared dataset located at `datasets/indian_infrastructure/irdid_prepared_classification/` contains image splits (`train: 466`, `val: 99`, `test: 105`), but lacks an explicit license file or written redistribution authorization.
- **Limitation:** Prior to staging or production deployment, municipal legal counsel must formally verify the original dataset provenance and confirm whether the IRDID license permits integration into public administration systems.

### 7.2 Model Performance & Statistical Limitations
- **Held-Out Test Sample Size:** Evaluated on 105 images (`broken_edges`: 11, `construction_zones`: 16, `cracks`: 23, `open_manholes`: 10, `potholes`: 30, `waterlogged_roads`: 15).
- **Broken Edges Low Recall:** Verified test recall is **63.64%** (7 TP, 4 FN out of 11 ground truth images). The classifier misses over 36% of road edge disintegration cases. It cannot be used as an autonomous filter without human verification.
- **Waterlogging Coarseness:** Verified test recall is **80.00%** (12 TP, 3 FN out of 15 ground truth images) and precision is **100.00%**. However, classification provides scene presence only; it does not measure water depth, flooded area, or vehicular passability.
- **Environmental Domain Shift:** Training images are predominantly daytime, dry-weather vehicle captures. Performance in active monsoon rain, low streetlight illumination, night conditions, and citizen smartphone optics remains unvalidated.

---

## 8. Deployment Approval Checklist

The following 9 approval gates must be formally satisfied and signed off before candidate weights may be activated in production:

- [ ] **Gate 1: Dataset Licensing Clearance**  
  Legal clearance verifying that the IRDID dataset license permits municipal civic operational use.
- [ ] **Gate 2: Cryptographic Checkpoint Integrity Verification**  
  Candidate checkpoint SHA-256 confirmed as `84637d53361e46522b87125fe4433fd619196a062d99db705fabcff379cccf45`.
- [ ] **Gate 3: Evaluation Artifact & Class Marginals Reconciliation**  
  Held-out test split of 105 images verified against confusion matrix column marginals `[11, 16, 23, 10, 30, 15]`.
- [ ] **Gate 4: Performance Criteria & Low-Recall Acceptance Approved**  
  Municipal stakeholder sign-off on 63.64% broken-edges recall with mandatory human verification triage.
- [ ] **Gate 5: Runtime Safeguards Implemented & Tested**  
  Feature flag (`ENABLE_IRDID_CLASSIFIER`), spatial precedence rule, and margin filtering implemented and passing tests.
- [ ] **Gate 6: YOLO & Manual-Reporting Regression Protection**  
  YOLO detector hash (`289e3e17...`) confirmed untouched; manual-reporting paths verified via automated test suite.
- [ ] **Gate 7: Zero Synthetic Bounding Boxes Confirmed**  
  Contract tests confirming `bounding_box: None` and `bounding_boxes: []` across all classification routes.
- [ ] **Gate 8: Rollback & Monitoring Protocol Documented**  
  $<30\text{s}$ rollback procedure via environment toggle tested and verified in staging environment.
- [ ] **Gate 9: Formal Human Deployment Authorization**  
  Written executive approval explicitly authorizing production deployment.

---

## 9. Final Verdict

### **STATUS: VERIFIED — READY FOR IMPLEMENTATION APPROVAL**

> **CRITICAL RESTRICTION NOTICE:**  
> This verdict certifies that forensic verification is complete, documentation and Git discrepancies are reconciled, and a rigorous implementation plan has been established.  
> **IT DOES NOT CONSTITUTE PERMISSION TO DEPLOY, ACTIVATE, COPY, RETRAIN, OR RUN INFERENCE WITH THE CLASSIFIER.**  
> The candidate model weights remain strictly **quarantined** at `runs\classify\runs\classify\irdid_cls_manual\weights\best.pt`. Production runtime directories remain empty. No code or configuration changes may be made without separate, explicit written authorization.
