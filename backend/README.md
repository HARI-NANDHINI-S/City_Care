# CivicVision AI — Backend Setup & Virtual Environment Guide

## Python Virtual Environment Setup Instructions

### On Windows (PowerShell):
```powershell
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

### On macOS / Linux:
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

---

## Running Backend Server
```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- Health Check Endpoint: `http://127.0.0.1:8000/api/v1/health`
- OpenAPI Docs: `http://127.0.0.1:8000/api/v1/docs`
