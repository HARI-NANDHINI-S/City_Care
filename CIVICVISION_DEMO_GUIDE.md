# CivicVision AI: Demonstration Guide

This guide details how to securely start the CivicVision AI platform on a native Windows environment, verify its subsystems, and demonstrate its features realistically to stakeholders.

## 1. Local Startup Instructions (Windows)

### Prerequisites
*   Python 3.10+
*   Node.js v18+

### Step 1: Start the Backend (FastAPI)
Open a terminal in the project root:
```powershell
cd backend
# Create/activate virtual environment if necessary
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# Start the server
$env:SECRET_KEY="demo_secret_key"
uvicorn app.main:app --reload
```
*Note: The backend runs on `http://127.0.0.1:8000` by default.*

### Step 2: Start the Frontend (Vite/React)
Open a new terminal in the project root:
```powershell
cd frontend
npm install
npm run dev
```
*Note: The frontend will automatically run on `http://localhost:5173` and proxy API calls to the backend.*

---

## 2. Platform Verification & Known Limitations

**Before presenting, ensure the database is intact.** 
1. Open the frontend at `http://localhost:5173`.
2. Login with `admin@civicvision.ai` (Password: `admin123`).
3. Check the Analytics dashboard to ensure metrics load.

### 🛑 Crucial Limitation: Real-time YOLO Inference (Windows AppLocker)
*   **The Constraint:** The host Windows OS Application Control policy actively intercepts and terminates the PyTorch dependency (`torch.dll`), physically preventing local machine learning execution.
*   **The Defense:** The application utilizes a highly resilient fail-safe. If inference is requested, the system catches the OS block and gracefully returns a HTTP 503 error instead of crashing. The frontend catches this, alerts the user ("Real YOLO model not available"), and disables submissions to prevent database pollution. 
*   **How to Explain This:** "Our YOLOv8 model is fully trained and integrated, but the current Windows enterprise security policy on this machine forbids its execution. However, you can see how robust our architecture is: instead of crashing the server, the backend intercepts the OS block, safely degrades, and prevents users from submitting invalid null-reports."

### 🛑 Crucial Limitation: Random Forest Predictions
*   **The Constraint:** The Random Forest model accurately predicts maintenance needs based on `PCI` and `AADT` features. However, the current municipal database lacks these inputs.
*   **The Defense:** Instead of inventing fake metrics to appear functional, the `/predictions` API correctly and honestly returns an `"unavailable"` state.
*   **How to Explain This:** "Our priority model is mathematically validated to work locally. But because our live database does not yet track complex metrics like PCI or Traffic Volume (AADT), the AI refuses to guess. It waits safely until we ingest official municipal data."

---

## 3. Recommended Demonstration Sequence

These workflows utilize **100% Real Persisted Data**, bypassing AI bottlenecks natively:

1.  **Citizen Reporting & Maps:**
    *   Log in as a citizen.
    *   Navigate to the interactive Map view to show serialized GIS data clustering.
    *   Show previous reports persisting in the "My Reports" dashboard.
2.  **Role-Based Security:**
    *   Log out and log in as `admin@civicvision.ai`.
    *   Show the comprehensive Admin Issue Management grid.
    *   Demonstrate sorting and status changes (e.g., transition an issue from `REPORTED` to `IN_PROGRESS`).
3.  **Analytics & Priority Engine:**
    *   Open the Dashboard.
    *   Explain the deterministic Priority Engine: since Random Forest is dormant, the system accurately relies on heuristic severity scoring (0.0-100.0) generated during report submission to rank municipal urgencies.
