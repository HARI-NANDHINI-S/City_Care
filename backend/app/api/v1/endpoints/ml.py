from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.issue import Issue
from app.ml.models import CivicVisionPriorityModels
from app.ml.shap_explain import ShapExplainer
from app.ml.dbscan import SpatialClustering
from app.ml.dataset import generate_synthetic_priority_dataset

router = APIRouter()

import os

@router.get("/evaluation")
def ml_evaluation():
    yolo_weights = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../ai_model/yolo/weights/best.pt"))
    rf_weights = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../ai_model/random_forest/weights/random_forest.joblib"))
    
    yolo_trained = os.path.exists(yolo_weights)
    rf_trained = os.path.exists(rf_weights)
    
    return {
        "yolo": {
            "trained": yolo_trained,
            "available": yolo_trained,
            "metrics": "evaluated" if yolo_trained else "unavailable"
        },
        "random_forest": {
            "trained": rf_trained,
            "available": rf_trained,
            "metrics": "evaluated" if rf_trained else "unavailable"
        }
    }

@router.get("/models")
def ml_models():
    yolo_weights = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../ai_model/yolo/weights/best.pt"))
    rf_weights = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../ai_model/random_forest/weights/random_forest.joblib"))
    
    yolo_trained = os.path.exists(yolo_weights)
    rf_trained = os.path.exists(rf_weights)
    
    return {
        "yolo": {
            "name": "YOLOv8 Detection",
            "trained": yolo_trained,
            "available": yolo_trained,
            "weights_path": yolo_weights if yolo_trained else None
        },
        "random_forest": {
            "name": "Random Forest Maintenance Prediction",
            "trained": rf_trained,
            "available": rf_trained,
            "weights_path": rf_weights if rf_trained else None
        }
    }

@router.get("/predictions/{issue_id}")
def ml_predictions(issue_id: int, db: Session = Depends(get_db)):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue: return {"error": "not found"}
    
    # Check Random Forest
    rf_weights = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../ai_model/random_forest/weights/random_forest.joblib"))
    rf_available = os.path.exists(rf_weights)
    
    rf_status = "not_available"
    rf_reason = "Required road-context features are unavailable"
    rf_maintenance_needed = None
    rf_probability = None
    
    # We do not have contextual features in DB right now, so we honestly report not_available
    # and don't invent synthetic ones.
    missing_features = ["PCI", "AADT", "Last Maintenance", "Average Rainfall", "Rutting", "IRI", "Road Type", "Asphalt Type"]
    
    return {
        "yolo": {
            "status": "success" if issue.ai_confidence > 0 else "not_available"
        },
        "random_forest": {
            "status": rf_status,
            "reason": f"{rf_reason}. Missing features: {', '.join(missing_features)}."
        },
        "priority": {
            "level": issue.severity.value if issue.severity else "Unknown",
            "score": issue.priority_score
        }
    }


@router.get("/explanations/{issue_id}")
def ml_explanations(issue_id: int, db: Session = Depends(get_db)):
    return {
        "status": "not_available",
        "reason": "SHAP explanations blocked. Missing trained Random Forest and real feature vectors."
    }

@router.get("/clusters")
def ml_clusters(db: Session = Depends(get_db)):
    issues = db.query(Issue).all()
    issues_list = []
    for issue in issues:
        issues_list.append({
            'id': issue.id,
            'latitude': issue.latitude,
            'longitude': issue.longitude,
            'issue_type': issue.issue_type.value if issue.issue_type else "Pothole",
            'priority_score': issue.priority_score
        })
    res = clustering.cluster_issues(issues_list)
    return res

@router.get("/lab/datasets")
def get_lab_datasets():
    return [
        {
            "id": "sf-pci-2023",
            "name": "San Francisco Pavement Condition Index (PCI) Scores",
            "source": "San Francisco Public Works / DataSF",
            "coverage": "San Francisco, CA, USA",
            "license": "Open Data (ODC-PDDL / Public Domain)",
            "status": "DOWNLOADED_AND_VERIFIED",
            "is_synthetic": False,
            "row_count": 19461,
            "column_count": 20,
            "columns": ["CNN", "Street_Name", "PCI_Score", "From_Street", "To_Street", "PCI_Change_Date", "Treatment_or_Survey", "Street_Accepted_For_Maintenance", "Functional_Class", "X", "Y", "Latitude", "Longitude", "Line", "Point", "Neighborhoods"],
            "target": "PCI_Score (Numeric 0-100)",
            "missing_values": "Low for key fields",
            "compatibility": "INCOMPATIBLE",
            "limitations": "Contains valid PCI target but strictly lacks requested structural predictors (AADT, rainfall, rutting). Blocked from use.",
            "link": "https://data.sfgov.org/api/views/5aye-4rtt/rows.csv?accessType=DOWNLOAD"
        },
        {
            "id": "synthetic-downstream",
            "name": "Synthetic Civic Prioritization Data",
            "source": "Internal Generator",
            "coverage": "Synthetic Pipeline",
            "license": "Internal",
            "status": "NOT_GENERATED",
            "is_synthetic": True,
            "row_count": 0,
            "column_count": 0,
            "columns": [],
            "target": "Priority Score",
            "missing_values": "N/A",
            "compatibility": "BLOCKED",
            "limitations": "Upstream models are untrained. Synthetic downstream data cannot be generated without genuine upstream predictions to avoid silent leakages.",
            "link": null
        }
    ]

@router.get("/lab/models")
def get_lab_models():
    # Return genuine status
    return [
        {
            "id": "random_forest",
            "name": "Random Forest",
            "task": "Pavement Maintenance Prediction (Classification)",
            "compatible_dataset": "None Verified",
            "target_variable": "Needs Maintenance",
            "readiness": "DATASET_NOT_READY",
            "training_status": "NOT_TRAINED",
            "dependency_status": "BLOCKED_ON_DATASET",
            "next_action": "Acquire Genuine India PCI/PMS Dataset",
            "features": ["PCI", "AADT", "Rutting", "IRI", "Rainfall", "Last Maintenance"],
            "preprocessing": "StandardScaler (Numeric), OneHotEncoder (Categorical)"
        },
        {
            "id": "decision_tree",
            "name": "Decision Tree",
            "task": "Pavement Maintenance Prediction (Classification)",
            "compatible_dataset": "None Verified",
            "target_variable": "Needs Maintenance",
            "readiness": "DATASET_NOT_READY",
            "training_status": "NOT_TRAINED",
            "dependency_status": "BLOCKED_ON_DATASET",
            "next_action": "Acquire Genuine India PCI/PMS Dataset",
            "features": ["PCI", "AADT", "Rutting", "IRI", "Rainfall", "Last Maintenance"],
            "preprocessing": "StandardScaler (Numeric), OneHotEncoder (Categorical)"
        },
        {
            "id": "logistic_regression",
            "name": "Logistic Regression",
            "task": "Pavement Maintenance Prediction (Classification)",
            "compatible_dataset": "None Verified",
            "target_variable": "Needs Maintenance",
            "readiness": "DATASET_NOT_READY",
            "training_status": "NOT_TRAINED",
            "dependency_status": "BLOCKED_ON_DATASET",
            "next_action": "Acquire Genuine India PCI/PMS Dataset",
            "features": ["PCI", "AADT", "Rutting", "IRI", "Rainfall", "Last Maintenance"],
            "preprocessing": "StandardScaler (Numeric), OneHotEncoder (Categorical)"
        },
        {
            "id": "gradient_boosting",
            "name": "Gradient Boosting",
            "task": "Pavement Maintenance Prediction (Classification)",
            "compatible_dataset": "None Verified",
            "target_variable": "Needs Maintenance",
            "readiness": "DATASET_NOT_READY",
            "training_status": "NOT_TRAINED",
            "dependency_status": "BLOCKED_ON_DATASET",
            "next_action": "Acquire Genuine India PCI/PMS Dataset",
            "features": ["PCI", "AADT", "Rutting", "IRI", "Rainfall", "Last Maintenance"],
            "preprocessing": "StandardScaler (Numeric), OneHotEncoder (Categorical)"
        }
    ]


