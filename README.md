# City Care 🏙️🤖

### AI-Powered Public Infrastructure Issue Detection & Resolution Platform

**City Care** is a professional, production-style Smart City digital platform built for final-year engineering portfolio and municipal infrastructure management.

Citizens can upload photos of public infrastructure defects (such as potholes, garbage accumulation, waterlogging, broken streetlights, open manholes, and road damage) along with location coordinates. The platform leverages **Computer Vision (Ultralytics YOLO + OpenCV)** to automatically detect issue classes, bounding box coordinates, and confidence scores, computes an **explainable priority score (0–100)**, automatically dispatches tickets to municipal departments, detects spatial/temporal duplicates using the **Haversine formula**, and tracks resolution history on interactive maps.

---

## 🌟 Key Features

1. **AI Vision Defect Inspection**: Automatically identifies 6 infrastructure issue classes (`Pothole`, `Garbage Accumulation`, `Waterlogging`, `Broken Streetlight`, `Open Manhole`, `Road Damage`) with bounding box overlays and confidence scores.
2. **Explainable Priority Scoring Engine**: Multi-factor 0–100 algorithm factoring in category risk weight, AI confidence score, defect bounding box area ratio, nearby duplicate report count, and unresolved aging hours.
3. **Automated Department Routing Matrix**: Configurable matrix routing defects to responsible municipal bodies (`Road & Public Works`, `Waste Management`, `Electrical Infrastructure`, `Stormwater Drainage`, `Sewerage Board`).
4. **Haversine Duplicate Detection**: Detects duplicate reports within a 50m geographical radius and 72-hour window to eliminate ticket clutter while escalating urgency.
5. **Interactive Public Issue Map**: Leaflet map interface with custom color-coded category markers, search filter toolbars, marker popups, and status indicators.
6. **Role-Based Access Control (RBAC)**:
   - **Citizen**: Register/Login, upload image, view AI inspection output, report issue, track status timeline, view my reports.
   - **Administrator**: Analytics dashboard with high-level KPIs, departmental workload tables, issue management, department reassignments, and status overrides.
   - **Department Officer**: Department-filtered queue with quick status progression controls (`REPORTED` → `AI_ANALYZED` → `UNDER_REVIEW` → `ASSIGNED` → `IN_PROGRESS` → `RESOLVED`).

---

## 🏗️ Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | React 18, Vite, TypeScript, Tailwind CSS, React-Leaflet, Lucide Icons, Axios |
| **Backend** | Python 3.10+, FastAPI, Pydantic v2, SQLAlchemy ORM, SQLite / PostgreSQL |
| **AI / Computer Vision** | Ultralytics YOLOv8 / YOLOv11, OpenCV (Headless), NumPy, Pillow |
| **Authentication** | OAuth2 JWT Bearer Tokens with PBKDF2-SHA256 Password Hashing |
| **Maps** | OpenStreetMap & Leaflet |

---

## 📁 Directory Structure

```
City Care/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # Auth, Issues, Departments, Analytics
│   │   ├── core/               # Security, Database Engine, Config
│   │   ├── models/             # User, Department, Issue, IssueImage, StatusHistory, Duplicate
│   │   ├── schemas/            # Pydantic Schemas
│   │   ├── services/           # AI Pipeline, Priority Engine, Routing, Duplicate Detector
│   │   ├── main.py             # FastAPI App Entrypoint
│   │   └── seed.py             # Database Seeding Script
│   ├── uploads/                # Original & AI Annotated Image Media
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/         # Navbar, PriorityBadge, StatusBadge, Map
│   │   ├── context/            # AuthContext
│   │   ├── pages/              # Landing, Login, Register, Report, Map, MyReports, Details, Admin, Officer
│   │   ├── services/           # Axios API Client
│   │   ├── types/              # TypeScript Types
│   │   ├── App.tsx             # React Router Setup
│   │   └── main.tsx
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
├── ai-model/
│   ├── dataset_spec.md         # Dataset & Training Specifications
│   └── model_loader.py         # PyTorch / ONNX Model Loader Interface
└── docs/
    └── ARCHITECTURE.md         # System Architecture Reference
```

---

## 🚀 Quick Start & Setup Guide

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ & npm

### 2. Backend Setup
```bash
# Navigate to project root
cd CivicVision-AI

# Install Python backend dependencies
pip install -r backend/requirements.txt

# Seed database with sample departments, users, and infrastructure issues
$env:PYTHONPATH="backend"  # On PowerShell (or export PYTHONPATH=backend on Linux/Mac)
python backend/app/seed.py

# Start FastAPI backend server
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- API Swagger Documentation: `http://127.0.0.1:8000/api/v1/docs`

---

### 3. Frontend Setup
```bash
# Navigate to frontend folder
cd frontend

# Install Node dependencies
cmd /c "npm install"

# Start Vite dev server
cmd /c "npm run dev"
```
- Open browser at: `http://localhost:5173`

---

## 🔐 Pre-Configured Demo Credentials

| Role | Email | Password | Access Rights |
| :--- | :--- | :--- | :--- |
| **Citizen** | `citizen@civicvision.ai` | `Citizen@123` | Upload issue images, view AI analysis, report issue, track reports |
| **Administrator** | `admin@civicvision.ai` | `Admin@123` | View KPI analytics, manage issues, reassign departments, audit status |
| **Department Officer (PWD)** | `pwd.officer@civicvision.ai` | `Officer@123` | View Road & Public Works issues, update resolution progress |
| **Department Officer (Sanitation)** | `sanitation.officer@civicvision.ai` | `Officer@123` | View Sanitation issues, update resolution progress |

---

## 🧪 Manual Verification Guide

1. **Test Citizen Issue Submission & AI Analysis**:
   - Log in as `citizen@civicvision.ai` / `Citizen@123` (or click the quick demo button on the login screen).
   - Navigate to **Report Issue**.
   - Upload any infrastructure image (e.g. sample pothole or road damage image).
   - Click **Run Instant AI Vision Analysis**.
   - Observe the OpenCV bounding box overlay image generated in real-time, detected class name, confidence score, severity rating, and recommended department routing.
   - Click **Fetch GPS Location** or adjust location details, then click **Submit Municipal Report**.
   - You will be redirected to the **Issue Details** page displaying the step-by-step status progress timeline.

2. **Test Public Issue Map**:
   - Navigate to **Public Map**.
   - Observe interactive Leaflet markers color-coded by issue type.
   - Click any map marker to inspect bounding box thumbnails, priority scores, and status badges.
   - Use the category and status dropdown filters to isolate specific issue types.

3. **Test Administrator Command Center**:
   - Log in as `admin@civicvision.ai` / `Admin@123`.
   - Navigate to **Admin Dashboard** to view total issues, open tickets, critical urgency counts, category distributions, and departmental performance tables.
   - Navigate to **Manage Issues** to view the full priority queue, reassign departments, or override statuses.

4. **Test Department Officer Workflow**:
   - Log in as `pwd.officer@civicvision.ai` / `Officer@123`.
   - Navigate to **Department Dashboard**.
   - Observe tickets assigned specifically to the *Road & Public Works Department*.
   - Click **In Progress** or **Mark Resolved** to update ticket status.
   - Log back in as a Citizen to verify the updated status on the citizen tracking timeline.
