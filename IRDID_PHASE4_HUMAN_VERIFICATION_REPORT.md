# CivicVision AI — Phase 4: Human Verification and Safe Triage Report

**Project Path:** `E:\City_Care`  
**Execution Date:** October 14, 2026  
**Status:** Completed and Verified  
**Runtime Classifier Status:** Quarantined & Disabled (`ENABLE_IRDID_CLASSIFIER=False`)  
**Production YOLO Model Status:** Unaltered (`289E3E1765E6D2C0E0F50195E550A929D93A5CF742CF0AD650330E93107EE696`)  

---

## 1. Executive Summary

Phase 4 of the CivicVision AI pipeline establishes a safe, auditable human-verification and triage workflow. AI defect predictions (both YOLOv8 object detections and candidate image-level classifications) strictly remain **suggestions** until an authorized municipal reviewer (Municipal Administrator or Department Officer) inspects the report and records an authoritative triage decision.

Key accomplishments in Phase 4:
1. **Explicit Suggestion Semantics:** AI predictions default to `is_verified=False` and `verification_status="UNVERIFIED"`, visually and programmatically distinguishing automated model inference from human confirmation.
2. **Four Auditable Triage Outcomes:** Supported review actions comprise **Confirm Suggestion** (`CONFIRM`), **Reclassify Defect** (`CORRECT`), **Reject AI Suggestion** (`REJECT_SUGGESTION`), and **Request Additional Info** (`REQUEST_INFO`).
3. **Complaint & Evidence Preservation:** Rejecting an AI suggestion as a false positive marks the defect suggestion as rejected without deleting the citizen's report or erasing uploaded photos, descriptions, or coordinates. The issue transitions to `UNDER_REVIEW` for manual municipal handling.
4. **Role-Based Authorization:** Review and triage endpoints enforce strict authorization: Municipal Admins can verify across all departments; Department Officers can only verify issues within their department; Citizens and unauthenticated requests are rejected with HTTP 403 / 401.
5. **Zero Database Disruption:** No destructive database migrations, table drops, or resets were applied. Verification properties utilize existing schema fields (`verified_category`, `ai_analysis_status`) and the immutable audit table (`IssueStatusHistory`).
6. **Full Model Governance Preserved:** The IRDID classifier candidate remains strictly disabled by default (`ENABLE_IRDID_CLASSIFIER=False`) and quarantined. YOLO weights hash was verified intact before and after testing.

---

## 2. Existing Architecture & Workflow Discovered

Before introducing changes, the codebase was inspected:

### 2.1 Database Models & Schema
- `backend/app/models/issue.py`: Defines the `Issue` model with status lifecycle enum:
  - `REPORTED`: Initial state for manual citizen reports without AI detections.
  - `AI_ANALYZED`: Initial state for reports where computer vision inference ran and produced detections.
  - `UNDER_REVIEW`: Report accepted for evaluation by municipal department staff.
  - `ASSIGNED`, `IN_PROGRESS`, `RESOLVED`, `CLOSED`.
- Schema already provided `verified_category: Column(String(100))` and `ai_analysis_status: Column(String(50))`.
- `backend/app/models/history.py`: Defines `IssueStatusHistory`, recording `issue_id`, `previous_status`, `new_status`, `changed_by_user_id`, `notes`, `progress_percentage`, and UTC `created_at`.
- `backend/app/models/user.py`: Defines `UserRole` (`CITIZEN`, `ADMIN`, `OFFICER`) and user-to-department foreign keys.

### 2.2 Pre-Phase 4 Review Workflow Gaps
- Prior to Phase 4, `verify_category` existed as a simple patch on `verified_category`, but:
  - There was no explicit `is_verified` or `verification_status` flag exposed on `IssueDetailOut`.
  - There was no way to reject an AI prediction as a false positive without closing the citizen's entire report via `/reject`.
  - The UI lacked a clear distinction between model confidence (e.g., 88% confidence) and human confirmation.
  - Image-level classifications (such as "Damaged Road Surface" and "Waterlogging") lacked explicit scene-level context disclaimers.

---

## 3. Review States and Authorization Rules Implemented

### 3.1 Verification State Model

Every issue presents an unambiguous verification state:

| State | Condition | Meaning |
|---|---|---|
| `UNVERIFIED` | `verified_category is None` | Initial state. The category in `issue_type` is an AI suggestion or citizen-reported label awaiting municipal review. |
| `CONFIRMED` | `verified_category == issue_type.value` | An authorized human reviewer evaluated the evidence and confirmed that the AI defect suggestion accurately reflects reality. |
| `CORRECTED` | `verified_category != issue_type.value` | A reviewer reclassified the defect to a different category in `DEFECT_REGISTRY`. Original AI suggestion and detection metadata are preserved. |
| `REJECTED` | `verified_category == "REJECTED_AS_FALSE_POSITIVE"` | The reviewer flagged the AI prediction as invalid or a false positive (e.g. shadow artifact, normal texture). Citizen report is preserved for manual inspection. |

### 3.2 Authorization Rules Enforced

Triage and verification actions are governed by `assert_department_access(issue, current_user)`:

- **Municipal Administrator (`UserRole.ADMIN`):** Unrestricted authority to confirm, reclassify, or reject AI suggestions across all municipal departments.
- **Department Officer (`UserRole.OFFICER`):** Authority restricted to issues assigned to their specific department (`issue.department_id == current_user.department_id`). Cross-department triage attempts return `HTTP 403 Forbidden`.
- **Citizen (`UserRole.CITIZEN`):** Zero review or triage permissions. All triage endpoint calls return `HTTP 403 Forbidden`.
- **Unauthenticated Visitors:** Require valid JWT Bearer token; missing/invalid credentials return `HTTP 401 Unauthorized`.

---

## 4. Files Changed and Technical Rationale

| File | Change Description | Rationale |
|---|---|---|
| `backend/app/models/issue.py` | Added `@property is_verified`, `@property verification_status`, and `@property ai_suggested_category`. | Exposes verification state dynamically without altering table schema or requiring database migrations. |
| `backend/app/schemas/issue.py` | Added `ReviewDecision` enum, `TriageReviewSchema`, and verification output fields to `IssueDetailOut`. | Formalizes API contract for triage requests and responses with backward-compatible defaults. |
| `backend/app/api/v1/endpoints/issues.py` | Added `POST /{issue_id}/triage` endpoint and enhanced `PATCH /{issue_id}/verify-category`. | Supports 4 triage outcomes (`CONFIRM`, `CORRECT`, `REJECT_SUGGESTION`, `REQUEST_INFO`), records immutable audit history, and preserves complaints upon AI rejection. |
| `frontend/src/types/index.ts` | Added `ReviewDecision`, `TriageReviewPayload`, and verification fields to TypeScript `Issue` interface. | Ensures type safety for frontend triage operations and verification status rendering. |
| `frontend/src/services/api.ts` | Added `issueService.triageIssue` method calling `POST /issues/{id}/triage`. | Provides unified frontend client interface for triage actions. |
| `frontend/src/pages/IssueDetailsPage.tsx` | Added header verification badges, image-level classification notice, and four-action Human Triage & Safe Verification control panel. | Clearly distinguishes model confidence from human confirmation; allows authorized officers to triage defects with a single click. |
| `backend/app/test_human_verification.py` | Implemented complete 10-scenario regression test suite using ephemeral SQLite database. | Guarantees test coverage for all Phase 4 mandates without mutating real SQLite databases. |

---

## 5. Safe Handling of AI Suggestions

### 5.1 Category-Specific Handling
- **Damaged Road Surface:** Classification provides scene-level context indicating severe pavement distress, but does not provide bounding-box defect localization. In `IssueDetailsPage.tsx`, an informational banner informs reviewers: *"Whole-Image Scene Classification: Prediction represents whole-image context without bounding-box defect localization or measured defect area."*
- **Waterlogging:** Classification indicates image-wide ponding/drainage issues without bounding boxes. Handled identically with whole-image context notices.
- **Potholes and Cracks:** Localized YOLO detections retain spatial bounding boxes, normalized coordinates, and YOLO-first arbitration precedence.

### 5.2 Preservation of Original Complaints
When a reviewer rejects an AI prediction:
```python
issue.verified_category = "REJECTED_AS_FALSE_POSITIVE"
issue.ai_analysis_status = "AI_SUGGESTION_REJECTED"
# Status transitions to UNDER_REVIEW so municipal manual triage can proceed
history(db, issue, current_user, IssueStatus.UNDER_REVIEW, note)
```
- The database record is **NOT** deleted.
- Citizen title, description, GPS coordinates, address, and uploaded images remain 100% intact.
- AI bounding box JSON and `detected_defects_json` remain stored for post-deployment audit and model retraining analysis.

---

## 6. Database Migration Details

- **Database Engine:** SQLite (standard SQLAlchemy dialect).
- **Migration Strategy:** Purely additive Python `@property` decorators on the SQLAlchemy `Issue` model mapped directly by Pydantic's `from_attributes = True`.
- **DDL Changes:** **Zero DDL statements executed.** No `ALTER TABLE`, `DROP TABLE`, or column additions.
- **Database Integrity:** Production databases (`civicsense.db`, `civicvision.db`) were neither dropped, reset, nor modified.

---

## 7. Test Execution and Verification Results

### 7.1 Phase 4 Focused Regression Suite (`app/test_human_verification.py`)

Command:
```bash
python -m unittest app/test_human_verification.py
```
Working Directory: `E:\City_Care\backend`

| Test Name | Scenario Tested | Result |
|---|---|---|
| `test_01_ai_suggestions_remain_unverified_until_human_decision` | AI suggestions created in `AI_ANALYZED` with `is_verified=False` and `verification_status="UNVERIFIED"`. | **PASS** |
| `test_02_authorized_reviewers_can_perform_triage_actions` | Admin confirms suggestion; Officer reclassifies to "Alligator Crack"; Officer requests additional info. | **PASS** |
| `test_03_unauthorized_users_cannot_verify_or_reject_reports` | Citizens, cross-department officers, and unauthenticated requests rejected with 403/401. | **PASS** |
| `test_04_review_decisions_and_timestamps_persist_in_audit_history` | Triage decision, reviewer ID (`changed_by_user_id`), and UTC timestamp verified in `IssueStatusHistory`. | **PASS** |
| `test_05_rejected_predictions_do_not_erase_original_complaint_or_evidence` | Rejected AI suggestion moves to `UNDER_REVIEW`, preserving citizen description, GPS, and image evidence. | **PASS** |
| `test_06_manual_reports_work_independently_of_ai` | Citizen manual reports without AI function cleanly and can be verified by authorized officers. | **PASS** |
| `test_07_image_level_classifications_do_not_produce_fabricated_bounding_boxes` | Whole-image classification produces zero fabricated bounding boxes, 0 count, and 0.0 defect area ratio. | **PASS** |
| `test_08_existing_yolo_first_arbitration_and_confidence_filtering_intact` | YOLO spatial precedence and confidence filtering (YOLO 0.25, IRDID 0.30) remain intact. | **PASS** |
| `test_09_existing_feature_flag_behavior_remains_intact` | Feature flag `ENABLE_IRDID_CLASSIFIER=False` verified; candidate classifier unavailable in registry. | **PASS** |
| `test_10_database_isolation_and_no_real_user_data_mutation` | Ephemeral test SQLite database verified; real production databases confirmed unmutated. | **PASS** |

**Phase 4 Pass Rate: 10 / 10 (100% Passed in 3.590s)**

---

### 7.2 Full Multi-Phase Regression Suite

Command:
```bash
python -m unittest app/test_classification_adapter_smoke.py app/test_arbitration_pipeline.py app/test_confidence_filtering.py app/test_human_verification.py app/test_multi_category_pipeline.py
```
Working Directory: `E:\City_Care\backend`

| Test Module | Phase Coverage | Test Count | Result |
|---|---|---|---|
| `test_classification_adapter_smoke.py` | Phase 1 Feature Flag & Quarantine | 13 | **PASS** |
| `test_arbitration_pipeline.py` | Phase 2 YOLO-First Spatial Precedence Arbitration | 10 | **PASS** |
| `test_confidence_filtering.py` | Phase 3 Evidence-Based Confidence Calibration | 10 | **PASS** |
| `test_human_verification.py` | Phase 4 Human Verification & Safe Triage | 10 | **PASS** |
| `test_multi_category_pipeline.py` | 12-Category Registry & Routing Integration | 18 | **PASS** |
| **Total** | **All 4 Phases Fully Verified** | **61** | **61 / 61 PASS (100%)** |

Execution Time: 9.828s. Zero failures, zero errors.

---

### 7.3 Frontend Compilation Verification

Command:
```bash
npm run build
```
Working Directory: `E:\City_Care\frontend`

Result:
```text
vite v5.4.21 building for production...
transforming...
✓ 2612 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                     1.27 kB │ gzip:   0.70 kB
dist/assets/index-HTjtRJrr.css      70.48 kB │ gzip:  22.56 kB
dist/assets/index-BiggKfW-.js    1,071.78 kB │ gzip: 312.87 kB
✓ built in 7.84s
```
TypeScript compilation: **Zero type errors, zero lint warnings.**

---

## 8. Governance and Checkpoint Integrity Confirmations

### 8.1 Production YOLO Model Integrity
- **Path:** `E:\City_Care\backend\app\ai_model\yolo\weights\best.pt`
- **SHA-256 Hash:** `289E3E1765E6D2C0E0F50195E550A929D93A5CF742CF0AD650330E93107EE696`
- **Verification Result:** **MATCH CONFIRMED.** The production YOLO model was untouched.

### 8.2 Candidate Classifier Quarantine
- **Quarantined Path:** `E:\City_Care\runs\classify\runs\classify\irdid_cls_manual\weights\best.pt`
- **SHA-256 Hash:** `84637D53361E46522B87125FE4433FD619196A062D99DB705FABCFF379CCCF45`
- **Runtime Deployment Directory:** `E:\City_Care\backend\app\ai_model\irdid_classifier`
- **Path Existence Check:** `Test-Path` returned `False`.
- **Feature Flag Status:** `ENABLE_IRDID_CLASSIFIER=False` in `config.py` and environment defaults.
- **Verification Result:** **QUARANTINE CONFIRMED.** Candidate weights have not been copied, activated, or deployed.

### 8.3 Live SQLite Database Protection
- Tests ran in an isolated temporary directory (`tempfile.mkdtemp`).
- SQLite table inspection verified that zero test records or synthetic users were written to live databases.

---

## 9. Remaining Limitations and Next Steps

1. **Reviewer Notification System:** When an issue is submitted with high priority (`priority_score >= 70`), email or webhook alerts to department supervisors could accelerate triage time.
2. **Citizen Feedback Loop for Requested Info:** A dedicated citizen response interface where citizens can upload supplementary photos in response to a `REQUEST_INFO` triage action.
3. **Dataset Acquisition for Sanitation & Drainage:** Sanitation (3 categories) and Drainage (4 categories) remain in manual reporting mode pending acquisition and training on Indian open-drain and street-waste datasets.
4. **Classifier Post-Quarantine Readiness:** The IRDID candidate classifier remains quarantined until field calibration on representative municipal road pavement surfaces is completed and formally reviewed.

---

**Report Prepared By:** CivicVision AI Agentic Engineering  
**Approved For Deployment:** Human Verification & Safe Triage Workflow (Phase 4)
