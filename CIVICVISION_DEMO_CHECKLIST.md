# CivicVision AI — Interactive Demonstration Checklist

**Target Location:** `E:\City_Care`  
**Application Architecture:** FastAPI (Python 3.10+) Backend + Vite React (Node.js 18+) Frontend  
**Audience:** Municipal Stakeholders, Technical Evaluators, Project Reviewers  
**Document Purpose:** A concise, step-by-step checklist to reliably demonstrate all core capabilities of the CivicVision AI platform during a live evaluation session.

---

## Pre-Demonstration: Available Accounts & Credentials

The platform includes pre-seeded demonstration accounts with role-based permissions:

| Persona | Email | Password | Access Rights & Views |
| :--- | :--- | :--- | :--- |
| **Citizen** | `citizen@civicvision.ai` | `Citizen@123` | Submit reports, view AI vision results, track personal tickets, respond to clarifications |
| **PWD Officer** | `pwd.officer@civicvision.ai` | `Officer@123` | Road & Public Works queue, review & triage potholes/cracks, update progress |
| **Sanitation Officer** | `sanitation.officer@civicvision.ai` | `Officer@123` | Waste Management queue, review & triage garbage accumulation tickets |
| **Administrator** | `admin@civicvision.ai` | `Admin@123` | Full municipal KPI analytics, cross-department reassignment, request citizen clarification |

> **Tip:** The login screen at `/login` provides one-click quick login buttons for each demo role.

---

## Step-by-Step Demonstration Workflow

### Stage 1: Application Startup & Health Check

1. **Start Backend Engine:**
   - Open a terminal in `E:\City_Care\backend`:
     ```powershell
     $env:PYTHONPATH="."
     python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
     ```
   - Verify health in browser or curl:
     - `GET http://127.0.0.1:8000/health` -> `{"status": "online", "database": "connected"}`
     - Swagger UI: `http://127.0.0.1:8000/api/v1/docs`

2. **Start Frontend Client:**
   - Open a second terminal in `E:\City_Care\frontend`:
     ```powershell
     npm run dev
     ```
   - Open browser at `http://localhost:5173`.
   - Confirm landing page loads with modern dark/cyan theme, KPI metrics, and navigation.

---

### Stage 2: Citizen Issue Submission & AI-Assisted Vision Analysis

1. **Log in as Citizen:**
   - Navigate to `http://localhost:5173/login`.
   - Click **Demo Citizen** (or enter `citizen@civicvision.ai` / `Citizen@123`).
   - You are redirected to `/dashboard` (Citizen Dashboard).

2. **Upload & Analyze Defect Photo:**
   - Click **Report Issue** in navbar or navigate to `http://localhost:5173/report`.
   - In the upload zone, drop a road damage or pothole photo (e.g. from `backend/uploads/original/` or your camera).
   - Click **Run Instant AI Vision Analysis**.
   - **Show Evaluators:**
     - Real-time YOLOv8 detection bounding box overlay.
     - Detected defect class (e.g., `Pothole`), confidence percentage, and recommended department (`Road & Public Works`).
     - Note the amber badge: **"AI Prediction (Unverified — Awaiting Human Verification)"**.

3. **Complete & Submit Report:**
   - Enter title: `Severe Road Hazard on Trunk Road`.
   - Enter description: `Deep pothole creating severe risk for two-wheelers.`
   - Click **Fetch GPS Location** (or enter coordinates: `13.0827`, `80.2707`).
   - Click **Submit Municipal Report**.
   - You are automatically redirected to the **Issue Details** page (`/issue/:id`).

---

### Stage 3: Issue Tracking & Public Issue Map

1. **Verify Citizen Tracking Timeline:**
   - On `/issue/:id`, observe the step-by-step progress tracker:
     - Step 1: `REPORTED` (Completed)
     - Step 2: `AI_ANALYZED` (Completed — Unverified AI Suggestion)
     - Step 3: `UNDER_REVIEW` (Pending)
   - Highlight the **Model Provenance** card displaying inference runtime, model version, and class scores.

2. **Inspect Public Issue Map:**
   - Navigate to `http://localhost:5173/map`.
   - Observe interactive OpenStreetMap markers color-coded by issue category.
   - Click the marker for the newly submitted pothole.
   - Inspect the popup showing AI confidence, priority score, address, and status.

---

### Stage 4: Department Officer Review, Triage & Verification

1. **Log in as PWD Officer:**
   - Log out from Citizen and log in as `pwd.officer@civicvision.ai` / `Officer@123`.
   - You are redirected to `/officer` (Department Officer Queue).
   - Confirm the newly reported issue appears at the top of the PWD department queue.

2. **Execute Human Triage:**
   - Click on the issue card to open `/issue/:id`.
   - In the **Municipal Triage Review** panel:
     - Click **CONFIRM**: Confirms the AI prediction matches reality.
     - (Alternative: Show **CORRECT** or **REJECT_SUGGESTION** to demonstrate false-positive handling).
     - Enter review note: `Inspected by PWD Zone 4 road squad. Pothole confirmed.`
     - Click **Submit Triage Decision**.
   - **Show Evaluators:**
     - Status updates to `UNDER_REVIEW`.
     - The verification badge turns **GREEN: CONFIRMED**.
     - An immutable entry is appended to the audit timeline with the officer's name and timestamp.

3. **Advance Lifecycle Progress:**
   - In the progress update panel, set progress to `50%` and note: `Asphalt crew on site. Compaction underway.`
   - Status automatically advances to `IN_PROGRESS`.
   - Update status to `RESOLVED` with note: `Pothole patched and cured. Road re-opened.`
   - Progress reaches `100%`.

---

### Stage 5: Citizen Feedback & Clarification Workflow

1. **Demonstrate Ambiguous Report Handling:**
   - Submit an ambiguous drainage issue as Citizen (or use an existing ticket).
   - Log in as Administrator (`admin@civicvision.ai` / `Admin@123`).
   - On the issue page, click **Request Clarification**.
   - Enter note: `Please confirm if water is overflowing from the main roadside channel or sidewalk kerb.`
   - Click **Send Clarification Request**.

2. **Citizen Response:**
   - Log back in as Citizen (`citizen@civicvision.ai`).
   - Go to `/my-reports` -> Notice the amber **Action Needed** indicator.
   - Open `/issue/:id` -> A prominent clarification banner appears with the officer's question.
   - Submit reply: `Overflow is coming from the sidewalk kerb inlet.`
   - Confirm the banner clears and the officer receives the reply in the timeline without prematurely verifying the issue.

---

### Stage 6: Security Boundary & Upload Protection Live Check

1. **Verify 10 MiB Upload Protection:**
   - Navigate to `/report`.
   - Attempt to upload an image exceeding 10 MiB (e.g. 11MB file).
   - **Show Evaluators:**
     - The application immediately blocks the upload with `HTTP 413 Request Entity Too Large` (`"Uploaded file exceeds maximum allowed size of 10MB"`).
     - Wire chunk streaming prevents server memory exhaustion.
     - Zero partial files are written to disk.

2. **Verify Extension Filtering:**
   - Attempt to upload a `.pdf` or `.exe` file.
   - **Show Evaluators:** Immediate rejection (`HTTP 400 Bad Request: "Invalid image format. Allowed: JPG, PNG, WEBP"`).

3. **Verify Role Authorization:**
   - Show that a Citizen cannot access `/admin` or `/officer` routes (redirects to `/map`).
   - Show that a Citizen cannot trigger officer triage APIs (`HTTP 403 Forbidden`).

---

### Stage 7: Shutdown & Cleanup

1. **Stop Dev Servers:**
   - In the backend terminal, press `Ctrl + C` to stop Uvicorn.
   - In the frontend terminal, press `Ctrl + C` to stop Vite.
2. **Data Preservation:**
   - Existing demonstration databases (`backend/civicsense.db` and `backend/civicvision.db`) remain fully intact with unmutated SHA-256 baselines.
