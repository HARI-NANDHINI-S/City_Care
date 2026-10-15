# CivicVision AI — Phase 4 Security and Persistence Audit Report

**Project:** `E:\City_Care`  
**Audit Date:** October 15, 2026  
**Scope:** Phase 4 Human Verification & Safe Triage Implementation  
**Auditor:** CivicVision AI Agentic Quality & Security Engineering  
**Overall Audit Status:** **PASSED (Zero Critical/High Vulnerabilities Remaining)**  
**Runtime Classifier Status:** Quarantined & Disabled (`ENABLE_IRDID_CLASSIFIER=False`)  
**Production YOLO Model Status:** Verified Unaltered (`289e3e1765e6d2c0e0f50195e550a929d93a5cf742cf0ad650330e93107ee696`)  
**Quarantined Classifier Status:** Verified Unaltered (`84637d53361e46522b87125fe4433fd619196a062d99db705fabcff379cccf45`)  

---

## 1. Executive Summary & Findings Classified by Severity

A comprehensive security, persistence, authorization, and audit-history integrity audit was conducted on the CivicVision AI Phase 4 Human Verification and Safe Triage subsystem. The audit evaluated database mappings, session lifecycles, authentication dependencies, role-based access controls, issue status transitions, triage semantics, and regression safety across all four project phases.

### Findings Classification Matrix

| Finding ID | Severity | Category | Description | Remediation / Verification Status |
|---|---|---|---|---|
| **FIND-01** | **Medium** | Persistence | Reviewer identity (`last_reviewed_by_name`) and review timestamp (`last_reviewed_at`) were stored in `issue_status_history` but were not directly exposed as first-class attributes on `Issue` / `IssueDetailOut`. | **RESOLVED:** Implemented safe `@property` getters on `Issue` reading from persisted `IssueStatusHistory`, exposed in Pydantic schema, and rendered in frontend UI without requiring any DDL schema change. |
| **FIND-02** | **Medium** | Triage Semantics | When an issue was triaged with `CONFIRM` or `CORRECT` after previously having its AI suggestion rejected (`AI_SUGGESTION_REJECTED`), `ai_analysis_status` remained `AI_SUGGESTION_REJECTED`, creating a contradictory model state. | **RESOLVED:** Updated `triage_issue` and `verify_category` to reconcile `ai_analysis_status` to `"SUCCESS"` when a reviewer confirms or reclassifies a defect. |
| **FIND-03** | **Low** | Audit Integrity | Repeated identical triage requests (e.g., duplicate clicks or network retries) unconditionally appended duplicate history entries into `issue_status_history`. | **RESOLVED:** Added idempotency detection in `triage_issue` and `verify_category` so identical requests without new notes or state changes return safely without appending redundant duplicate history rows. |
| **FIND-04** | **Informational** | AI Preservation | `ai_suggested_category` property did not explicitly list `AI_SUGGESTION_REJECTED` in recognized states, risking loss of original AI suggestion display on rejected reports. | **RESOLVED:** Added `AI_SUGGESTION_REJECTED` to the recognized analysis status list in `Issue.ai_suggested_category`. |
| **FIND-05** | **Informational** | Governance | Verify that production YOLO checkpoint and candidate classifier weights remained strictly quarantined and unaltered throughout testing. | **VERIFIED:** Hashes recalculated and verified identical to canonical SHA-256 values; runtime deployment directory absent. |

---

## 2. Persistence Findings and Remediation

### 2.1 Dynamic Properties Investigation

| Property | Investigation Method | Determination | Persistence Mechanism |
|---|---|---|---|
| `is_verified` | Code & Session Reload Inspection | **Persisted / Safely Derived** | Derived deterministically from persisted column `issues.verified_category`. Evaluates to `True` if `verified_category` is non-null and not `"REJECTED_AS_FALSE_POSITIVE"`. |
| `verification_status` | Code & Session Reload Inspection | **Persisted / Safely Derived** | Derived deterministically from persisted column `issues.verified_category` and `issues.issue_type`. Yields `"UNVERIFIED"`, `"CONFIRMED"`, `"CORRECTED"`, or `"REJECTED"`. |
| `ai_suggested_category` | Code & Session Reload Inspection | **Persisted / Safely Derived** | Derived deterministically from persisted columns `issues.issue_type`, `issues.ai_confidence`, `issues.ai_analysis_status`, and `issues.detected_defects_json`. Preserved across reclassification and false positive rejection. |
| Reviewer Identity | Multi-Session Test (`test_11`) | **Persisted in DB** | Persisted immutably in `issue_status_history.changed_by_user_id` (foreign key to `users.id`). Exposed safely via `Issue.last_reviewed_by_name`. |
| Review Timestamp | Multi-Session Test (`test_11`) | **Persisted in DB** | Persisted immutably in `issue_status_history.created_at` (UTC timestamp). Exposed safely via `Issue.last_reviewed_at`. |

### 2.2 Application Restart & Session Isolation Verification
Test `test_11_persistence_across_separate_sessions_and_simulated_restart` in `backend/app/test_human_verification.py` simulates a complete application restart:
1. An issue is submitted by a citizen and analyzed with AI confidence `0.89`.
2. A PWD officer triages the issue with `CONFIRM`.
3. All active database sessions and connection pools are closed and disposed.
4. A brand new SQLAlchemy engine and session are instantiated against the database file.
5. The issue and its joined relationships are loaded cleanly from disk.
6. **Result:** `verified_category`, `is_verified`, `verification_status`, `ai_suggested_category`, `last_reviewed_by_name`, and `last_reviewed_at` all evaluate accurately and serialize through `IssueDetailOut.model_validate(issue)` without loss.

### 2.3 Database Safety & Zero-Migration Guarantee
- **Database Engine:** SQLite (unchanged).
- **Destructive Changes:** Zero. No tables were dropped, recreated, truncated, or reset.
- **DDL Changes:** Zero schema alterations were required against the live databases. All audit and verification data leverage existing schema fields (`verified_category: Column(String(100))` and `issue_status_history`).
- **Live Database State:** Live database files `civicsense.db` and `app/civicvision.db` were inspected before and after testing; their timestamps, file sizes, and record counts remained completely untouched.

---

## 3. Authorization Audit

Authorization for `POST /api/v1/issues/{id}/triage`, `PATCH /api/v1/issues/{id}/verify-category`, and helper `assert_department_access` was audited against all 7 mandatory test cases:

| Case | Scenario | Expected Result | Audit Result | Verification Mechanism |
|---|---|---|---|---|
| **Case 1** | Unauthenticated request without JWT bearer token | HTTP 401 Unauthorized | **PASS** | Enforced by FastAPI dependency `current_user: User = Depends(get_current_user)`. |
| **Case 2** | Citizen attempts triage or verification action | HTTP 403 Forbidden | **PASS** | Enforced by `assert_department_access`: role `CITIZEN` rejected (`current.role not in (ADMIN, OFFICER)`). |
| **Case 3** | Municipal Administrator reviews issue in any department | HTTP 200 OK | **PASS** | Administrator role permitted across all department boundaries. |
| **Case 4** | Department Officer reviews issue in assigned department | HTTP 200 OK | **PASS** | Officer permitted when `current.department_id == issue.department_id`. |
| **Case 5** | Department Officer attempts review of an issue from another department | HTTP 403 Forbidden | **PASS** | Enforced by `assert_department_access`: `issue.department_id != current.department_id` raises 403 with message `"Issue is outside your department"`. |
| **Case 6** | Request changes `issue_id` to tamper with another issue | HTTP 404 / 403 | **PASS** | Non-existent ID returns 404; cross-department ID returns 403 before any mutation occurs. |
| **Case 7** | Missing, malformed, or unexpected role or department data | HTTP 403 / 422 | **PASS** | Officers without department (`not current.department_id`) or unassigned issues fail safely with 403; invalid payload fails with 422. |

---

## 4. Audit-History Integrity & Triage Semantics

### 4.1 Audit History Guarantees
1. **Append-Only Immutability:** Review actions write new entries to `issue_status_history` recording `issue_id`, `previous_status`, `new_status`, `changed_by_user_id`, `notes`, `progress_percentage`, and UTC `created_at`. Previous entries are never updated or deleted.
2. **Failure Isolation:** Any unauthorized or invalid request (401, 403, 404, 400, 422) raises an `HTTPException` prior to `db.commit()`, guaranteeing that failed review requests cannot modify issue data or create misleading history records.
3. **Idempotency on Redundant Requests:** Repeated identical triage requests (same decision, same verified category, matching notes) do not insert redundant duplicate rows into `issue_status_history` without an explicit reason (`test_12`). When a reviewer provides new notes or a new decision, an audit history entry is recorded.
4. **Privacy Protection:** No user passwords, authentication tokens, session identifiers, or unnecessary personal data are recorded in audit notes.

### 4.2 Triage Actions Semantics

| Decision | State Change | Citizen Complaint Preservation | AI Metadata Preservation |
|---|---|---|---|
| `CONFIRM` | `verified_category = confirmed_cat`<br>`status = UNDER_REVIEW`<br>`is_verified = True` | Preserved intact (title, description, coordinates, photos untouched). | Preserved intact (`issue_type`, `ai_confidence`, bounding boxes, defect area). |
| `CORRECT` | `verified_category = new_cat`<br>`status = UNDER_REVIEW`<br>`is_verified = True` | Preserved intact. Reviewer notes explain reclassification rationale. | Preserved intact. Original suggestion preserved in `issue_type` and `detected_defects_json`. |
| `REJECT_SUGGESTION` | `verified_category = "REJECTED_AS_FALSE_POSITIVE"`<br>`ai_analysis_status = "AI_SUGGESTION_REJECTED"`<br>`status = UNDER_REVIEW`<br>`is_verified = False` | **Preserved intact.** Report is NOT closed or deleted; remains queued under review for manual municipal inspection. | Preserved intact. Model confidence and bounding box data remain accessible for audit. |
| `REQUEST_INFO` | `status = UNDER_REVIEW`<br>`latest_update = note`<br>`is_verified` unchanged | Preserved intact. Citizen report remains active while awaiting clarification. | Preserved intact. |

---

## 5. Files Changed and Technical Rationale

| File Path | Changes Made | Technical Rationale |
|---|---|---|
| `backend/app/models/issue.py` | 1. Added `@property last_reviewed_at` and `@property last_reviewed_by_name` derived safely from `status_history`.<br>2. Updated `ai_suggested_category` property to include `AI_SUGGESTION_REJECTED`.<br>3. Cleaned EOF formatting. | Exposes reviewer identity and review timestamps without requiring DDL schema modifications; preserves AI suggestion after false positive rejection. |
| `backend/app/schemas/issue.py` | Added `last_reviewed_at: Optional[datetime] = None` and `last_reviewed_by_name: Optional[str] = None` to `IssueDetailOut`. | Exposes reviewer audit metadata through the REST API response contract with automatic Pydantic validation. |
| `backend/app/api/v1/endpoints/issues.py` | 1. Added idempotency detection in `triage_issue` and `verify_category` to prevent duplicate history records on repeated identical calls.<br>2. Reconciled `ai_analysis_status` to `"SUCCESS"` when confirming or correcting a previously rejected suggestion. | Enforces audit history integrity (no duplicate records without explicit reason) and prevents contradictory verification states. |
| `frontend/src/types/index.ts` | Added `last_reviewed_at?: string | null;` and `last_reviewed_by_name?: string | null;` to the `Issue` TypeScript interface. | Aligns frontend TypeScript types with the updated backend API contract. |
| `frontend/src/pages/IssueDetailsPage.tsx` | Added display of reviewer full name and review timestamp in the Verification Status banner. | Provides municipal reviewers and staff immediate visibility of who performed triage and when. |
| `backend/app/test_human_verification.py` | Added test scenarios 11 through 14 covering multi-session persistence, application restart simulation, idempotency, state contradiction safety, and cross-department auth tampering. | Comprehensive automated regression coverage for all audit criteria. |

---

## 6. Exact Test Commands and Results

### 6.1 Backend Test Suite (All 5 Project Test Modules)

**Command:**
```powershell
& "C:\Users\HARI NANDHINI\AppData\Local\Programs\Python\Python314\python.exe" -m unittest `
  app.test_classification_adapter_smoke `
  app.test_arbitration_pipeline `
  app.test_confidence_filtering `
  app.test_human_verification `
  app.test_multi_category_pipeline
```
**Working Directory:** `E:\City_Care\backend`  
**Execution Time:** 10.214 seconds  

**Results Summary:**
```text
Ran 65 tests in 10.214s

OK
```

**Test Suite Breakdown:**
- `app.test_classification_adapter_smoke`: 13 / 13 **PASS** (Feature flag gating, classifier disabled by default, quarantine verification)
- `app.test_arbitration_pipeline`: 10 / 10 **PASS** (YOLO-first spatial precedence over scene-level classification)
- `app.test_confidence_filtering`: 10 / 10 **PASS** (Evidence-based threshold filtering, edge cases, fallback to manual)
- `app.test_human_verification`: 14 / 14 **PASS** (Triage actions, multi-session persistence, app restart, idempotency, auth tampering)
- `app.test_multi_category_pipeline`: 18 / 18 **PASS** (Active 12-category defect registry, department routing, readiness labels)
- **Total:** **65 / 65 PASS (100% Success Rate)**

### 6.2 Frontend Production Compilation

**Command:**
```powershell
npm run build
```
**Working Directory:** `E:\City_Care\frontend`  
**Execution Time:** 7.91 seconds  

**Results Output:**
```text
> civicvision-ai-frontend@1.0.0 build
> tsc && vite build

vite v5.4.21 building for production...
transforming...
✓ 2612 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                     1.27 kB │ gzip:   0.70 kB
dist/assets/index-DBgwQfpN.css      70.59 kB │ gzip:  22.58 kB
dist/assets/index-DdkzK2v-.js    1,073.04 kB │ gzip: 312.98 kB
✓ built in 7.91s
```
**TypeScript Verification:** **Zero type errors, zero compile warnings.**

---

## 7. Database Safety Verification

Live SQLite database files were audited to verify that no destructive operations, record deletions, schema resets, or test mutations occurred:

| Database File | File Size (Bytes) | Last Modified Timestamp | Issue Records Count | User Records Count | Mutation Check |
|---|---|---|---|---|---|
| `E:\City_Care\backend\civicsense.db` | 126,976 | 12-10-2026 23:15:15 | 1 | 6 | **UNCHANGED** |
| `E:\City_Care\backend\app\civicvision.db` | 122,880 | 10-10-2026 18:39:06 | 2 | 2 | **UNCHANGED** |

All tests strictly operated in isolated, ephemeral SQLite databases created via `tempfile.mkdtemp` and cleaned up during `tearDownClass`.

---

## 8. YOLO and Classifier Checkpoint Integrity Verification

Cryptographic SHA-256 hashes of both models were calculated directly from the filesystem and compared against the established baseline:

### 8.1 Production YOLOv8 Model
- **File Path:** `E:\City_Care\backend\app\ai_model\yolo\weights\best.pt`
- **Expected SHA-256:** `289e3e1765e6d2c0e0f50195e550a929d93a5cf742cf0ad650330e93107ee696`
- **Calculated SHA-256:** `289E3E1765E6D2C0E0F50195E550A929D93A5CF742CF0AD650330E93107EE696`
- **Integrity Status:** **EXACT MATCH CONFIRMED.** Production model is unaltered.

### 8.2 Quarantined IRDID Classifier Candidate
- **File Path:** `E:\City_Care\runs\classify\runs\classify\irdid_cls_manual\weights\best.pt`
- **Expected SHA-256:** `84637d53361e46522b87125fe4433fd619196a062d99db705fabcff379cccf45`
- **Calculated SHA-256:** `84637D53361E46522B87125FE4433FD619196A062D99DB705FABCFF379CCCF45`
- **Integrity Status:** **EXACT MATCH CONFIRMED.** Quarantined model is unaltered.

### 8.3 Runtime Directory Quarantine Check
- **Runtime Classifier Directory:** `E:\City_Care\backend\app\ai_model\irdid_classifier`
- **Directory Existence Check:** `Test-Path` returned `False`.
- **Default Feature Flag:** `ENABLE_IRDID_CLASSIFIER=False` in `backend/app/core/config.py`.
- **Quarantine Status:** **CONFIRMED STRICTLY QUARANTINED.** No weights have been copied into runtime paths.

---

## 9. Remaining Limitations and Blockers

1. **No Classifier Deployment Until Field Calibration:** The IRDID six-class image classifier candidate remains quarantined and disabled by default. It must not be deployed until field calibration on representative municipal road pavement surfaces is completed and formally approved.
2. **Citizen Multi-Turn Communication:** When a reviewer triggers `REQUEST_INFO`, the issue remains in `UNDER_REVIEW` with an explanatory note. Future phases may add an interactive citizen messaging panel allowing supplementary photo uploads in response to specific reviewer inquiries.
3. **Dataset Acquisition for Remaining Domains:** Sanitation (3 classes) and Drainage (4 classes) remain in manual reporting mode pending collection of Indian municipal drainage and solid waste datasets.

---

## 10. Audit Sign-Off

The CivicVision AI Phase 4 Human Verification and Safe Triage implementation meets all security, persistence, authorization, audit-history integrity, and regression-safety requirements. Zero critical or high vulnerabilities remain. Phase 5 must not be started until authorized by project leadership.

**Audit Completed By:** CivicVision AI Agentic Security Audit  
**Status:** **AUDIT PASSED / CERTIFIED SECURE**
