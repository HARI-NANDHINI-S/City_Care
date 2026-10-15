# CivicVision AI — Root Cause Investigation & Fix Report
## AI Category Detection, False Pothole Mitigation, and Map Restoration

**Project Path:** `E:\City_Care`  
**Date:** October 15, 2026  
**Status:** All Fixes Implemented, Validated, and Regression Tested (101/101 Tests Passing)

---

## 1. Executive Summary

This engineering report documents the root-cause analysis, architecture correction, and empirical validation for two critical defects in CivicVision AI:
1. **False Pothole Predictions & Category Locking:** The reporting workflow repeatedly identified uploaded images as potholes—even when images showed normal roads, non-road defects, or sanitation/drainage issues—and prevented citizens from reporting other categories.
2. **Broken Map Feature:** The public infrastructure map suffered from missing Leaflet styling in offline/restricted environments, lack of dynamic map container sizing, missing auto-bounds fitting, and absence of proxy configuration in preview environments.

Both defects have been completely resolved with targeted, surgical fixes. The platform now honestly supports **all 15 municipal reporting categories**, enforces **genuine YOLOv8 detection** strictly on the 4 road damage classes it was trained on, displays transparent **Category Disagreements** when AI and citizen selections diverge, and renders an interactive, robust, Leaflet-powered GIS map.

---

## 2. Root Cause Analysis

### 2.1 Bug 1: False Pothole Predictions & Category Hijacking
* **Root Cause A (Frontend State Default):** In `frontend/src/pages/ReportIssuePage.tsx`, the `manualCategory` state was initialized to `'Pothole'`:
  ```tsx
  const [manualCategory, setManualCategory] = useState<string>('Pothole');
  ```
  Crucially, the category selection dropdown was hidden from the citizen during initial upload. It was only rendered when the AI returned `status: 'no_detection'`. Because it was pre-set to `'Pothole'`, any image with no road defect (e.g. a normal road, clean pavement, garbage dump, open manhole, or streetlight) defaulted to **"Pothole"** upon submission.
* **Root Cause B (Forced AI Category Overwrite):** In `ReportIssuePage.tsx`, line 98 previously enforced:
  ```tsx
  const effectiveCategory = isManualMode ? manualCategory : aiResult?.issue_type;
  ```
  Whenever the AI produced a detection (even a low-confidence false positive `D40` on asphalt texture), the UI hid the manual selector completely and forcibly set the issue type to `aiResult.issue_type`, leaving the citizen unable to choose or correct their category.
* **Root Cause C (Missing Categories in Selector):** The previous manual selector only enumerated 12 categories, omitting `Open Manhole`, `Broken Streetlight`, and `Road Damage`, preventing citizens from reporting utility hazards.
* **Root Cause D (Hardcoded Fallback in Endpoints):** In `backend/app/api/v1/endpoints/ml.py` line 205, clustering logic fell back to `'Pothole'` if `issue.issue_type` was null. In `backend/app/services/ai_service.py`, if valid detections lacked spatial boxes, `max([])` risked a `ValueError`.

### 2.2 Bug 2: Map Failure & Incomplete Rendering
* **Root Cause A (Missing Leaflet CSS in Bundle):** `PublicIssueMapPage.tsx` did not import `leaflet/dist/leaflet.css`. The application relied exclusively on a remote CDN link (`unpkg.com`) in `index.html`. Under offline, restricted, or high-latency network conditions, Leaflet tile panes and markers were rendered without CSS, causing markers to stack at coordinate $(0,0)$ and tiles to shatter or disappear.
* **Root Cause B (Container Sizing & Invalidation):** In `PublicIssueMapPage.tsx`, `<MapContainer>` was embedded inside a flex container without an explicit minimum pixel height or size invalidation hook. In React, Leaflet calculates initial container dimensions before layout completes, causing the map to render as a gray canvas.
* **Root Cause C (Missing Zoom Controls & Static Center):** The map hardcoded `zoomControl={false}` and `center={[28.6139, 77.2090]}` without fitting bounds to actual database issue markers.
* **Root Cause D (Vite Preview Proxy Gap):** In `frontend/vite.config.ts`, only `server.proxy` was defined. When running production previews (`npm run preview`), `/api` and `/uploads` requests failed with 404 Not Found.

---

## 3. Supported Reporting Categories & AI Boundary

CivicVision AI distinguishes **AI-Detected Classes** from **Citizen Reporting Categories** and **Department Routing**:

| # | Municipal Category | Domain | AI Detection Capability | Responsible Department |
|---|---|---|---|---|
| 1 | **Pothole** | Road | **YOLOv8 Supported** (`D40`) | Road & Public Works Dept (`DEPT_PWD`) |
| 2 | **Longitudinal Crack** | Road | **YOLOv8 Supported** (`D00`) | Road & Public Works Dept (`DEPT_PWD`) |
| 3 | **Transverse Crack** | Road | **YOLOv8 Supported** (`D10`) | Road & Public Works Dept (`DEPT_PWD`) |
| 4 | **Alligator Crack** | Road | **YOLOv8 Supported** (`D20`) | Road & Public Works Dept (`DEPT_PWD`) |
| 5 | **Damaged Road Surface** | Road | Manual Citizen Reporting (Classifier Quarantined) | Road & Public Works Dept (`DEPT_PWD`) |
| 6 | **Road Damage (Legacy)** | Road | Manual Citizen Reporting (Umbrella Category) | Road & Public Works Dept (`DEPT_PWD`) |
| 7 | **Garbage Accumulation** | Sanitation | Manual Citizen Reporting (Pending Training) | Waste Management & Sanitation (`DEPT_SAN`) |
| 8 | **Illegal Dumping** | Sanitation | Manual Citizen Reporting (Pending Training) | Waste Management & Sanitation (`DEPT_SAN`) |
| 9 | **Overflowing Garbage Bins** | Sanitation | Manual Citizen Reporting (Pending Training) | Waste Management & Sanitation (`DEPT_SAN`) |
| 10 | **Blocked Drains** | Drainage | Manual Citizen Reporting (Field Data Required) | Stormwater Drainage Dept (`DEPT_DRAIN`) |
| 11 | **Overflowing Drains** | Drainage | Manual Citizen Reporting (Field Data Required) | Stormwater Drainage Dept (`DEPT_DRAIN`) |
| 12 | **Waterlogging** | Drainage | Manual Citizen Reporting (Classifier Quarantined) | Stormwater Drainage Dept (`DEPT_DRAIN`) |
| 13 | **Damaged Drainage Covers** | Drainage | Manual Citizen Reporting (Field Data Required) | Stormwater Drainage Dept (`DEPT_DRAIN`) |
| 14 | **Open Manhole** | Utility | Manual Citizen Reporting (Safety Critical) | Sewerage & Sanitation Board (`DEPT_SEW`) |
| 15 | **Broken Streetlight** | Utility | Manual Citizen Reporting (Electrical Safety) | Electrical Infrastructure Dept (`DEPT_ELEC`) |

---

## 4. Files Modified & Technical Rationale

| File Path | Nature of Change | Technical Rationale |
|---|---|---|
| `backend/app/services/ai_service.py` | Empty detection safety guard | Prevents `ValueError: max() arg is an empty sequence` when no detections have valid bounding boxes; returns explicit `no_detection` dictionary. |
| `backend/app/api/v1/endpoints/ml.py` | Fallback cleanup | Replaced hardcoded `"Pothole"` default with `"Uncategorized"` when clustering issues lacking `issue_type`. |
| `backend/app/api/v1/endpoints/issues.py` | Map-data coordinate sanitization | Validates numeric range ($-90 \le \text{lat} \le 90$, $-180 \le \text{lng} \le 180$) and casts coordinates to float, safely skipping malformed records. |
| `frontend/vite.config.ts` | Preview proxy configuration | Added `preview.proxy` matching `server.proxy` so `npm run preview` seamlessly routes `/api` and `/uploads` to backend port 8000. |
| `frontend/src/types/index.ts` | Type expansion & category export | Added `'Utility'` to `DefectCategoryMeta.domain` and exported `ALL_15_CATEGORIES` with full metadata and capability declarations. |
| `frontend/src/pages/PublicIssueMapPage.tsx` | Map rendering & Leaflet fixes | Imported `leaflet/dist/leaflet.css`, added `MapController` (`invalidateSize()` + `fitBounds()`), added zoom controls, coordinate validation, 15-category colors, and empty/error banners. |
| `frontend/src/pages/ReportIssuePage.tsx` | Honest 15-category reporting & disagreement UI | Provided upfront 15-category selection, eliminated silent pothole defaults, added Category Disagreement cards with citizen override buttons, and preserved manual reporting. |
| `frontend/src/pages/IssueDetailsPage.tsx` | Officer reclassification expansion | Updated the officer `CORRECT` category selector to include all 15 categories. |
| `backend/app/test_ai_and_map_fixes.py` | New regression test suite | 10 dedicated automated test cases verifying AI detection, normal road behavior, 15-category routing, disagreement preservation, and map sanitization. |

---

## 5. Before vs. After Behavior

| Scenario | Before Fix | After Fix |
|---|---|---|
| **Normal road image uploaded** | Backend returned `no_detection`. Frontend defaulted `manualCategory` to `'Pothole'`, submitting the issue as a Pothole with title `"Pothole Report"`. | Backend returns `no_detection`. Frontend displays an informative banner: *"No road defect detected by computer vision"*. The report proceeds with the citizen's chosen category (e.g., Damaged Road Surface) and routes correctly. |
| **Garbage / Streetlight / Utility report** | Hidden manual selector; if YOLO detected a faint crack or road texture in background, the category was locked to Pothole. | Citizen chooses category upfront from all 15 options. If non-road, UI explains automated vision is not applicable. Image is uploaded and routed directly to `DEPT_SAN` or `DEPT_ELEC`. |
| **AI / Citizen category mismatch** | AI prediction silently replaced the citizen's selection. | UI shows **Category Disagreement Detected** card showing both Citizen choice and AI detection, offering two explicit buttons: `Keep My Category` or `Accept AI Suggestion`. |
| **Public Map loading** | Failed or rendered blank/shattered tiles without internet; container height was unconstrained; no zoom controls; markers stacked at $(0,0)$ if CSS failed. | `leaflet.css` bundled locally; `MapController` invalidates size and auto-fits bounds; zoom controls available; invalid coordinates filtered; all 15 categories color-coded. |
| **Vite Preview mode** | `/api/v1/issues/map-data` returned 404 because `preview.proxy` was missing. | `preview.proxy` configured; map data loads identically in dev and production preview. |

---

## 6. Empirical Test Verification

### 6.1 Automated Test Execution
- **Command:** `python -m unittest discover -s app -p "test_*.py"` (Working Directory: `E:\City_Care\backend`)
- **Total Tests Run:** **101 tests**
- **Failures / Errors:** **0**
- **Exit Code:** `0 (OK)`
- **Execution Time:** 16.898 seconds

### 6.2 New AI & Map Test Suite (`app.test_ai_and_map_fixes`)
- `test_01_model_loading_and_class_consistency`: PASSED (Loads `best.pt`, verifies 4 classes `D00`, `D10`, `D20`, `D40`).
- `test_02_normal_road_image_no_fabricated_pothole`: PASSED (Solid asphalt produces `status='no_detection'`, `issue_type=None`).
- `test_03_invalid_corrupted_image_handling`: PASSED (Corrupt bytes produce `status='analysis_failed'`).
- `test_04_supported_road_defect_pothole_detection`: PASSED (Real `img0001.jpg` yields `Pothole`, confidence $43.8\%$).
- `test_05_supported_road_defect_crack_detection`: PASSED (Real `img0204.jpg` yields `Longitudinal Crack`).
- `test_06_department_routing_for_all_15_categories`: PASSED (All 15 categories map to valid department codes).
- `test_07_manual_reporting_for_non_yolo_categories`: PASSED (Garbage -> `DEPT_SAN`, Manhole -> `DEPT_SEW`, Streetlight -> `DEPT_ELEC`).
- `test_08_disagreement_citizen_override_preserved`: PASSED (Preserves citizen category and records `CITIZEN_OVERRODE_AI`).
- `test_09_map_data_endpoint_validation_and_sanitization`: PASSED (All returned points have valid float coordinates).
- `test_10_map_data_skips_invalid_coordinates`: PASSED (Records with lat $999.0$ are excluded from map points).

### 6.3 Frontend Production Build
- **Command:** `npm run build` (Working Directory: `E:\City_Care\frontend`)
- **Result:** `✓ built in 9.46s` (TypeScript compiled with 0 errors).

---

## 7. Data Safety and System Integrity Audit

| Artifact / Metric | Pre-Fix Baseline | Post-Fix Final | Integrity Status |
|---|---|---|---|
| `backend/civicsense.db` SHA-256 | `A71082F97057E1356AB7BA02F6E8EA17C8C9AB13B94C54CEB1C547D18D70B85F` | `A71082F97057E1356AB7BA02F6E8EA17C8C9AB13B94C54CEB1C547D18D70B85F` | **100% Unchanged** |
| `backend/civicvision.db` SHA-256 | `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855` | `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855` | **100% Unchanged** |
| `best.pt` Model Weights SHA-256 | `289E3E1765E6D2C0E0F50195E550A929D93A5CF742CF0AD650330E93107EE696` | `289E3E1765E6D2C0E0F50195E550A929D93A5CF742CF0AD650330E93107EE696` | **100% Unchanged** |
| `ENABLE_IRDID_CLASSIFIER` | `False` | `False` | **Preserved** |
| Database Schema | SQLite SQLAlchemy | SQLite SQLAlchemy | **No Schema Changes** |

---

## 8. Remaining Limitations & Boundaries

1. **Computer Vision Scope:** The loaded YOLOv8 model (`best.pt`) was trained on Indian Road Damage Dataset (RDD2020) and genuinely detects 4 road defect classes (`Pothole`, `Longitudinal Crack`, `Transverse Crack`, `Alligator Crack`). Non-road categories (Sanitation, Drainage, Utilities) operate via citizen manual reporting. No synthetic or fake model predictions have been fabricated.
2. **OpenStreetMap Tile Provider:** Leaflet connects to public OpenStreetMap tiles (`https://{s}.tile.openstreetmap.org`). In air-gapped environments without internet access, tile images cannot be fetched; however, map controls, container geometry, and issue markers render without crashing.

---

## 9. How to Run the Fixed Application

### Step 1: Start the Backend REST API
Open a PowerShell terminal:
```powershell
cd E:\City_Care\backend
$env:PYTHONPATH="."
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
- Health Check: `http://127.0.0.1:8000/health`
- Interactive API Docs: `http://127.0.0.1:8000/api/v1/docs`

### Step 2: Start the Frontend Client
Open a second PowerShell terminal:
```powershell
cd E:\City_Care\frontend
npm run dev
```
- Web Application URL: `http://localhost:5173`
- Public Issue Map URL: `http://localhost:5173/map`
- Report Issue Wizard: `http://localhost:5173/report`

### Step 3: Demonstration Accounts
- **Citizen:** `citizen@civicvision.ai` / `Citizen@123`
- **PWD Officer:** `pwd.officer@civicvision.ai` / `Officer@123`
- **Sanitation Officer:** `sanitation.officer@civicvision.ai` / `Officer@123`
- **Administrator:** `admin@civicvision.ai` / `Admin@123`
