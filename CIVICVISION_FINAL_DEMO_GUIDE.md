# CivicVision AI — Final Live Demonstration Guide

**Project:** `E:\City_Care`  
**Target Environment:** Windows 11 Enterprise (Native Python 3.10+ & Node.js 18+ Runtimes)  
**Author:** Antigravity Autonomous Systems & Quality Assurance Agent  
**Purpose:** Comprehensive, reliable, step-by-step instructions for running an interactive live demonstration of CivicVision AI during academic project defenses and stakeholder reviews.

---

## 1. System Requirements & Prerequisites

| Requirement | Supported Version | Verification Command | Notes |
| :--- | :--- | :--- | :--- |
| **Python** | Python 3.10 to 3.14+ | `python --version` | Standard Python runtime on PATH |
| **Node.js** | Node.js v18.0.0+ | `node --version` | Required for Vite frontend |
| **npm** | npm v9.0.0+ | `npm --version` | Package manager |
| **Database** | SQLite 3 (Built-in) | Verified via Python | Persistent file `backend/civicsense.db` |
| **Computer Vision** | Ultralytics YOLOv8 | Verified via PyTorch | Model weights in `backend/app/ai_model/yolo/weights/best.pt` |

---

## 2. Startup Instructions & Service URLs

### 2.1 Backend Engine Startup

1. Open a PowerShell terminal and navigate to the project directory:
   ```powershell
   cd E:\City_Care\backend
   ```
2. Set the Python module search path:
   ```powershell
   $env:PYTHONPATH="."
   ```
3. Start the FastAPI Uvicorn server:
   ```powershell
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
4. **Health Check Validation:**
   - Base Route: `http://127.0.0.1:8000/` -> Expected: `{"message": "Welcome to CivicVision AI API", "status": "running"}`
   - Service Health: `http://127.0.0.1:8000/health` -> Expected: `{"status": "online", "database": "connected"}`
   - Interactive Swagger API Documentation: `http://127.0.0.1:8000/api/v1/docs`

### 2.2 Frontend Client Startup

1. Open a second PowerShell terminal:
   ```powershell
   cd E:\City_Care\frontend
   ```
2. Start the Vite development server:
   ```powershell
   npm run dev
   ```
3. **Frontend URL:** `http://localhost:5173`
   - Alternatively, to demonstrate the production build preview:
     ```powershell
     npm run build
     npm run preview -- --port 4173
     ```
     URL: `http://localhost:4173`

---

## 3. Demo Accounts & Role-Based Credentials

The application includes pre-seeded demonstration accounts. The login screen at `/login` provides one-click quick demo buttons:

| Role | Email | Password | Intended Workflow |
| :--- | :--- | :--- | :--- |
| **Citizen** | `citizen@civicvision.ai` | `Citizen@123` | Submit defect reports, upload photos, view AI inference, track personal status, reply to clarifications |
| **PWD Officer** | `pwd.officer@civicvision.ai` | `Officer@123` | Road & Public Works Department queue, review and triage potholes and road defects, update progress |
| **Sanitation Officer** | `sanitation.officer@civicvision.ai` | `Officer@123` | Waste Management Department queue, review and triage garbage accumulation tickets |
| **Administrator** | `admin@civicvision.ai` | `Admin@123` | Municipal overview, department reassignment, request citizen clarification, view system KPIs |

---

## 4. Repeatable Demonstration Scenario

### Step 1: Citizen Authentication
- **Action:** In your browser, navigate to `http://localhost:5173/login`.
- **UI Interaction:** Click the cyan **Citizen** quick-demo card (populates `citizen@civicvision.ai` / `Citizen@123`), then click **Sign In**.
- **Expected Visible Result:** Instant redirection to the Public Map (`/map`) or Citizen Dashboard (`/dashboard`) showing active user session as "Ananya Verma (Citizen)".

---

### Step 2: Citizen Issue Submission & AI-Assisted Vision Analysis
- **Action:** Click **Report Issue** in the top navigation bar (navigates to `/report`).
- **UI Interaction:**
  1. Under **"Upload Defect Image"**, upload a real test road defect image:
     - Recommended demo image: select [`backend/uploads/original/083a1b3b103d403399f4f30ab0ad7440.jpg`](file:///E:/City_Care/backend/uploads/original/083a1b3b103d403399f4f30ab0ad7440.jpg) (a 44.3 KiB image from the dataset).
  2. Click **Run Instant AI Vision Analysis**.
- **Expected Visible Result:**
  - Real-time YOLOv8 bounding box overlay appears with class tag `Pothole`.
  - Detection panel displays:
    - **Detected Defect:** `Pothole` (Model ID: `yolov8-rdd2020-india-v1`)
    - **Confidence Score:** ~`32.1%` (calibrated against Indian road conditions)
    - **Recommended Routing:** `Road & Public Works Department` (`DEPT_PWD`)
    - **Severity Assessment:** `MEDIUM`
  - A prominent amber badge states: **"AI Prediction (Unverified — Awaiting Human Verification)"**.
- **Demonstration Talking Point:** Emphasize that the AI prediction is purely an aid. The citizen can change the category dropdown manually if the model made an error.

---

### Step 3: Complete & Submit the Report
- **UI Interaction:**
  1. Set Title: `Severe Pothole on Anna Salai Highway`.
  2. Set Description: `Hazardous pothole causing vehicular congestion and hazard to two-wheelers.`
  3. Click **Fetch GPS Location** or enter coordinates: Latitude `13.0827`, Longitude `80.2707`.
  4. Address: `Anna Salai, Chennai`.
  5. Click **Submit Municipal Report**.
- **Expected Visible Result:**
  - Redirection to the newly created Issue Details page (`/issue/:id`).
  - Progress tracker shows Step 1 (`REPORTED`) and Step 2 (`AI_ANALYZED`) completed.
  - The issue status is displayed as `AI_ANALYZED`, with an amber **UNVERIFIED** badge.

---

### Step 4: Issue Tracking in Citizen Dashboard
- **Action:** Click **My Reports** in the navbar (`/my-reports`).
- **Expected Visible Result:**
  - The submitted pothole ticket appears at the top of the list with thumbnail, priority score badge, and status `AI_ANALYZED`.
- **Action:** Click **Public Map** (`/map`).
- **Expected Visible Result:**
  - An interactive Leaflet map pin appears at coordinates (13.0827, 80.2707).
  - Clicking the pin opens a popup showing the bounding-box thumbnail, category `Pothole`, priority score, and unverified status badge.

---

### Step 5: Department Officer Review & Human Triage
- **Action:** Log out from Citizen and navigate to `/login`.
- **UI Interaction:** Click the indigo **Officer** quick-demo card (`pwd.officer@civicvision.ai` / `Officer@123`), then click **Sign In**.
- **UI Navigation:** Navigate to `/officer` (Department Officer Dashboard).
- **Expected Visible Result:**
  - The officer queue displays tickets filtered exclusively for `Road & Public Works Department`.
  - The newly submitted pothole ticket is visible with an action button **Review & Triage**.
- **Action:** Click on the ticket to open `/issue/:id`.
- **UI Interaction in Triage Panel:**
  1. The officer inspects the citizen photo and YOLO bounding box.
  2. Select Decision: **CONFIRM** (Validates that the defect matches reality).
     *(Alternative demonstration: show CORRECT to reclassify, or REJECT to flag false positive).*
  3. Enter Review Notes: `Inspected by PWD Zone 4 road maintenance squad. Pothole confirmed.`
  4. Click **Submit Triage Decision**.
- **Expected Visible Result:**
  - Status updates to `UNDER_REVIEW`.
  - Verification badge turns **GREEN: CONFIRMED**.
  - A new immutable audit entry is added to the **Resolution History Timeline** showing the reviewer's name (`Rajesh Sharma (PWD Lead)`) and timestamp.

---

### Step 6: Department Lifecycle Progression
- **UI Interaction:**
  1. In the **Update Progress** panel, set Progress Slider to `50%`.
  2. Enter Progress Note: `Asphalt patch crew deployed. Surface prepped.`
  3. Click **Update Progress** -> Status updates to `IN_PROGRESS`.
  4. In the **Status Update** panel, select `RESOLVED`.
  5. Enter Note: `Pothole resurfacing complete. Road reopened to traffic.`
  6. Click **Mark Resolved**.
- **Expected Visible Result:**
  - Status updates to `RESOLVED` with `100%` progress.
  - Timeline displays 4 sequential milestones: `REPORTED` -> `UNDER_REVIEW` -> `IN_PROGRESS` -> `RESOLVED`.

---

### Step 7: Citizen Clarification & Feedback Loop
- **Action:** Log in as Administrator (`admin@civicvision.ai` / `Admin@123`).
- **UI Interaction:**
  1. Open any pending ticket.
  2. Click **Request Clarification**.
  3. Enter Note: `Please confirm whether waterlogging is near the bus shelter or sidewalk kerb.`
  4. Click **Submit Request**.
- **Action:** Log back in as Citizen (`citizen@civicvision.ai`).
- **Expected Visible Result:**
  - In `/my-reports`, the issue displays an amber **Clarification Requested** badge.
  - Opening the ticket reveals a prominent clarification banner with the reviewer's question and a reply textarea.
  - Submitting a reply appends the citizen's response to the timeline without falsely resolving the ticket.

---

### Step 8: Security Protection Demonstration
- **Action:** As Citizen, navigate to `/report`.
- **Demonstration:**
  1. **Upload Size Limit:** Attempt to upload an image exceeding 10 MiB (e.g. 11MB file).
     - **Observed Result:** Application immediately returns `HTTP 413 Request Entity Too Large` (`"Uploaded file exceeds maximum allowed size of 10MB"`). Wire chunk streaming halts transfer and cleans up disk immediately.
  2. **Disallowed Extensions:** Attempt to upload a `.pdf`, `.sh`, or `.exe` file.
     - **Observed Result:** Rejected with `HTTP 400 Bad Request` (`"Invalid image format. Allowed: JPG, PNG, WEBP"`).
  3. **Role Authorization:** Attempt to access `/admin` or `/officer` while logged in as a Citizen.
     - **Observed Result:** Access blocked; automatically redirected to `/map`.

---

## 5. Common Failure Symptoms & Safe Recovery

| Symptom | Probable Cause | Safe Recovery Procedure |
| :--- | :--- | :--- |
| **Backend fails with `ModuleNotFoundError: No module named 'app'`** | `PYTHONPATH` not configured | In backend terminal, run: `$env:PYTHONPATH="."` before starting uvicorn. |
| **Port 8000 already in use (`Errno 10048`)** | A previous Uvicorn instance is still running | Find and terminate the process: `Get-Process python \| Stop-Process` or use an alternative port. |
| **Frontend displays "Network Error" on login** | Backend server is not running or blocked | Ensure backend Uvicorn is active at `http://127.0.0.1:8000/health`. |
| **Leaflet Map tiles not loading** | Machine has no active internet connection | OpenStreetMap requires internet access to render raster map tiles. Ensure Wi-Fi/Ethernet is connected. |
| **Upload returns HTTP 413** | File size exceeds 10 MiB limit | Select an image file smaller than 10 MiB (e.g. 1MB–5MB phone photo). |

---

## 6. Shutdown & Cleanup Procedure

1. In the backend terminal, press `Ctrl + C` to cleanly stop Uvicorn.
2. In the frontend terminal, press `Ctrl + C` to stop the Vite server.
3. Demonstration databases (`backend/civicsense.db` and `backend/civicvision.db`) remain fully intact with unmutated SHA-256 baselines.
