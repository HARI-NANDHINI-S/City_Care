# CivicVision AI — Phase 5: Citizen Feedback and Manual-Review Workflow Report

**Project:** `E:\City_Care`  
**Date:** October 15, 2026  
**Status:** COMPLETED & VERIFIED  

---

## Executive Summary

Phase 5 delivers a secure, bidirectional clarification workflow between citizen reporters and municipal reviewers without breaking report integrity, bypassing role-based access control, or conflating citizen feedback with administrative verification. 

When municipal reviewers require supplementary information or photos (`REQUEST_INFO`), the report remains strictly in `UNDER_REVIEW`. The citizen report owner receives real-time visibility and actionable prompts on their dashboard, report list, tracking page, and detail view. Citizens can submit written clarifications and supplementary photo evidence. Crucially, a citizen response **never** marks an issue verified or resolved; the ticket remains under review for municipal officer determination.

All 74 automated regression and feature tests pass (`OK`), and the frontend compiles cleanly (`tsc && vite build` exited with code 0).

---

## 1. Existing Architecture & Baseline Inspection

Prior to Phase 5:
- **Phase 4 Capabilities:** Introduced human verification triage (`CONFIRM`, `CORRECT`, `REJECT_SUGGESTION`, `REQUEST_INFO`), verified category tracking, reviewer identity logging, and audit history.
- **Identified Gap:** While `REQUEST_INFO` recorded a note in the audit history and kept the report in `UNDER_REVIEW`, citizens had no structured, secure mechanism to:
  1. View pending clarification inquiries directed specifically to their report.
  2. Provide a structured response or upload supplementary evidence.
  3. Track whether their response was received.
  4. Distinguish an internal administrative review note from citizen-facing clarification requests.

---

## 2. Implemented Architecture & Workflow

### 2.1 Additive Data Model: `IssueClarification`
To ensure data safety, we implemented a non-destructive, additive table [`IssueClarification`](file:///e:/City_Care/backend/app/models/clarification.py) instead of modifying existing issue tables:

```python
class IssueClarification(Base):
    __tablename__ = "issue_clarifications"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id", ondelete="CASCADE"), nullable=False, index=True)
    request_text = Column(Text, nullable=False)
    requested_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    response_text = Column(Text, nullable=True)
    response_image_path = Column(String(500), nullable=True)
    responded_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="PENDING", nullable=False)  # PENDING | RESPONDED
```

- **Relationships & Properties:**
  - `Issue.clarifications`: Relationship ordered chronologically (`order_by="IssueClarification.created_at"`).
  - `Issue.has_pending_clarification`: Fast boolean property indicating whether any clarification record on the issue is currently in `"PENDING"` status.
  - `IssueClarification.requested_by_name`: Safely exposes the reviewer's display name without leaking internal credentials or admin notes.

---

## 3. Backend Endpoints & Strict Authorization Controls

All endpoints enforce strict RBAC via `assert_owner_or_authorized` and `assert_department_access` in [`backend/app/api/v1/endpoints/issues.py`](file:///e:/City_Care/backend/app/api/v1/endpoints/issues.py):

| Endpoint | Method | Permitted Roles | Description & Safety Enforcements |
| :--- | :---: | :---: | :--- |
| `/api/v1/issues/clarifications/pending` | `GET` | Authenticated Citizen | Returns all reports owned by the caller that have pending clarification requests. |
| `/api/v1/issues/{issue_id}/clarifications` | `GET` | Report Owner, Admin, Assigned Dept Officer | Returns chronological clarification history for an issue. Other citizens receive `403 Forbidden`. |
| `/api/v1/issues/{issue_id}/clarifications` | `POST` | Admin, Assigned Dept Officer | Issues a new clarification request directed to the citizen. Automatically sets status to `PENDING`. |
| `/api/v1/issues/{issue_id}/clarifications/{clarification_id}/respond` | `POST` | **Report Owner Only** | Validates `current_user.id == issue.reporter_id`. Records response text and optional photo. Updates status to `RESPONDED`. **Safety Guard:** Does **not** set `is_verified=True` or change `status` from `UNDER_REVIEW`. |
| `/api/v1/issues/{issue_id}/triage` | `POST` | Admin, Assigned Dept Officer | When decision is `REQUEST_INFO`, automatically creates an `IssueClarification(status="PENDING")`. |

### Key Authorization Guards:
1. **Owner-Only Responses:** Attempting to respond to another citizen's clarification request returns `403 Forbidden` (`"Only the citizen who reported this issue can respond to clarification requests"`).
2. **Reviewer-Only Inquiries:** Citizens attempting to issue a clarification request receive `403 Forbidden` (`"Not enough permissions"`).
3. **Internal Note Isolation:** `IssueClarificationOut` schema contains only the inquiry prompt, requester name, timestamp, and citizen response. Administrative audit logs and reviewer notes remain segregated.

---

## 4. Report Status Transparency & UI Improvements

We improved visibility across both citizen and municipal interfaces while preserving the underlying lifecycle status model (`REPORTED` → `AI_ANALYZED` → `UNDER_REVIEW` → `ASSIGNED` → `IN_PROGRESS` → `RESOLVED` → `CLOSED`):

1. **Clarification Status Badge (`StatusBadge.tsx`):**
   - Displays an amber `Action Required: Clarification Requested` badge when `hasPendingClarification` is true.
2. **Citizen Dashboard (`CitizenDashboardPage.tsx`):**
   - Renders a prominent amber Alert Banner whenever `pendingClarifications.length > 0`, with a direct action button linking to the report needing attention.
3. **My Reports View (`MyReportsPage.tsx`):**
   - Displays an `Action Required: Clarification Requested` chip on affected tickets so citizens immediately spot reports needing input.
4. **Issue Detail Page (`IssueDetailsPage.tsx`):**
   - **Report Owner View:** When a clarification is pending, renders a dedicated response panel with inquiry text, timestamp, response textarea, optional supplementary photo path, and submission button.
   - **Reviewer & Public History:** Displays an ordered thread of all inquiries and responses with timestamps and status tags (`PENDING` vs `RESPONDED`).
   - **AI vs Human Decision Clarity:** Retains clear distinction between AI suggestion badges and authorized human verification decisions (`✓ Human Verified: Confirmed` vs `✎ Reclassified` vs `✕ Suggestion Rejected`).
5. **Issue Tracking Page (`IssueTrackingPage.tsx`):**
   - Highlights the `UNDER_REVIEW` step with clarification notices and pending action callouts.

---

## 5. Manual-Review Workflow & 12 Defect Categories

CivicVision AI's category registry and triage capabilities were verified for all 12 registered categories across 3 municipal domains:

```
Road Infrastructure Defects (5):
  1. Pothole                   [YOLO Object Detection Supported]
  2. Longitudinal Crack        [YOLO Object Detection Supported]
  3. Transverse Crack          [YOLO Object Detection Supported]
  4. Alligator Crack           [YOLO Object Detection Supported]
  5. Damaged Road Surface      [Classification Intended — Quarantined / Inactive]

Sanitation & Waste Defects (3) — Pure Manual Review:
  6. Garbage Accumulation      [Manual Reporting Only — Pending Model Training]
  7. Illegal Dumping           [Manual Reporting Only — Pending Model Training]
  8. Overflowing Garbage Bins  [Manual Reporting Only — Pending Model Training]

Drainage & Flood Defects (4) — Pure Manual Review:
  9. Blocked Drains            [Manual Reporting Only — Insufficient Field Data]
 10. Overflowing Drains        [Manual Reporting Only — Insufficient Field Data]
 11. Waterlogging              [Classification Intended — Quarantined / Inactive]
 12. Damaged Drainage Covers   [Manual Reporting Only — Insufficient Field Data]
```

- **Safety Guarantee:** Manual reporting is preserved for sanitation and drainage categories without automated detection.
- No synthetic bounding boxes, automated severity scores, or fabricated measurements are generated.
- Whole-image scene classification notices are explicitly rendered in the UI for whole-image classes.

---

## 6. Model Governance & Data Safeguards

All model governance constraints were strictly adhered to:
1. `ENABLE_IRDID_CLASSIFIER=false` remains the default across all environments.
2. The candidate IRDID classifier remains quarantined; no weights were loaded or deployed.
3. Production YOLO-first arbitration and confidence thresholds remain unmodified.
4. Zero synthetic data generated; zero training executions initiated.
5. Production SQLite databases (`civicsense.db` and `civicvision.db`) were **not** modified or replaced. All tests were executed on isolated temporary SQLite databases.
6. Checkpoint hashes verified unchanged:
   - YOLO (`best.pt`): `289e3e1765e6d2c0e0f50195e550a929d93a5cf742cf0ad650330e93107ee696`
   - IRDID candidate (`resnet50_irdid_best.pth`): `84637d53361e46522b87125fe4433fd619196a062d99db705fabcff379cccf45`
   - `civicsense.db`: `E9C1414C8CC02266977412B80E0767487FE29511C513A1F2644CD7270A8EF23A`
   - `civicvision.db`: `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`

---

## 7. Verification & Test Results

### 7.1 Backend Test Suite (74/74 Passed in 12.16s)
Executed via:
```powershell
python -m unittest app.test_classification_adapter_smoke app.test_arbitration_pipeline app.test_confidence_filtering app.test_human_verification app.test_multi_category_pipeline app.test_citizen_feedback -v
```

**Results Breakdown:**
- `app.test_citizen_feedback` (8/8 PASSED):
  - `test_01_citizen_views_only_own_clarification_requests` — **OK**
  - `test_02_citizen_responds_to_own_request` — **OK**
  - `test_03_another_citizen_cannot_respond_to_request` — **OK** (403 Forbidden verified)
  - `test_04_unauthorized_users_cannot_issue_clarifications` — **OK** (403 Forbidden verified)
  - `test_05_clarification_history_persists_across_separate_sessions` — **OK**
  - `test_06_citizen_response_does_not_verify_or_resolve` — **OK** (`is_verified=False`, status `UNDER_REVIEW`)
  - `test_07_original_ai_metadata_and_complaint_intact` — **OK** (confidence, predictions, photos preserved)
  - `test_08_existing_auth_triage_and_routing_unchanged` — **OK**
- `app.test_human_verification` (15/15 PASSED) — **OK**
- `app.test_multi_category_pipeline` (18/18 PASSED) — **OK**
- `app.test_confidence_filtering` (11/11 PASSED) — **OK**
- `app.test_arbitration_pipeline` (11/11 PASSED) — **OK**
- `app.test_classification_adapter_smoke` (11/11 PASSED) — **OK**

**Total: 74 tests run, 0 failures, 0 errors.**

### 7.2 Frontend Production Build
Executed via:
```powershell
cd frontend && npm run build
```
**Result:**
- TypeScript compiler (`tsc`): 0 errors.
- Vite build: transformed 2612 modules into production bundles in 6.96s.
- Exit code: `0`.

---

## 8. Summary of Files Changed

| File | Change Description |
| :--- | :--- |
| [`backend/app/models/clarification.py`](file:///e:/City_Care/backend/app/models/clarification.py) | **Created:** Additive `IssueClarification` model for tracking citizen clarifications. |
| [`backend/app/models/__init__.py`](file:///e:/City_Care/backend/app/models/__init__.py) | Registered `IssueClarification` in models export. |
| [`backend/app/models/issue.py`](file:///e:/City_Care/backend/app/models/issue.py) | Added `clarifications` relationship and `has_pending_clarification` property. |
| [`backend/app/schemas/issue.py`](file:///e:/City_Care/backend/app/schemas/issue.py) | Added `IssueClarificationOut`, `CitizenClarificationResponseSchema`, `RequestClarificationSchema`. |
| [`backend/app/api/v1/endpoints/issues.py`](file:///e:/City_Care/backend/app/api/v1/endpoints/issues.py) | Added endpoints for pending clarifications, issue clarifications, responding, and triage integration. |
| [`backend/app/test_citizen_feedback.py`](file:///e:/City_Care/backend/app/test_citizen_feedback.py) | **Created:** 8 comprehensive security and workflow unit tests. |
| [`frontend/src/types/index.ts`](file:///e:/City_Care/frontend/src/types/index.ts) | Added `IssueClarification` interface and updated `Issue` type. |
| [`frontend/src/services/api.ts`](file:///e:/City_Care/frontend/src/services/api.ts) | Added clarification endpoints to `issueService` and `citizenService`. |
| [`frontend/src/components/common/StatusBadge.tsx`](file:///e:/City_Care/frontend/src/components/common/StatusBadge.tsx) | Added support for `hasPendingClarification` badge. |
| [`frontend/src/pages/CitizenDashboardPage.tsx`](file:///e:/City_Care/frontend/src/pages/CitizenDashboardPage.tsx) | Added pending clarifications alert banner. |
| [`frontend/src/pages/MyReportsPage.tsx`](file:///e:/City_Care/frontend/src/pages/MyReportsPage.tsx) | Added clarification action-required indicator. |
| [`frontend/src/pages/IssueDetailsPage.tsx`](file:///e:/City_Care/frontend/src/pages/IssueDetailsPage.tsx) | Added citizen clarification inquiry response form and history thread. |
| [`frontend/src/pages/IssueTrackingPage.tsx`](file:///e:/City_Care/frontend/src/pages/IssueTrackingPage.tsx) | Added clarification status banner and timeline stage annotations. |
| [`frontend/src/pages/OfficerDashboardPage.tsx`](file:///e:/City_Care/frontend/src/pages/OfficerDashboardPage.tsx) | Enhanced department task queue with clarification indicators. |
| [`frontend/src/pages/AdminIssueManagementPage.tsx`](file:///e:/City_Care/frontend/src/pages/AdminIssueManagementPage.tsx) | Added clarification status indicator to municipal administrative table. |

---

## 9. Remaining Limitations & Next Steps

1. **Physical File Upload for Responses:** Clarification responses currently accept a supplementary image path/URL string. When cloud object storage (e.g. S3/MinIO) is configured in Phase 6, a direct multipart upload endpoint can be coupled with this workflow.
2. **Push Notifications:** Clarification requests currently trigger in-app dashboard badges and status flags. Email/SMS/Push notifications can be integrated with worker queues in future phases.
3. **Model Classifier Activation:** The candidate classifier remains safely quarantined per governance requirements until field validation datasets for non-road classes are curated and certified.
