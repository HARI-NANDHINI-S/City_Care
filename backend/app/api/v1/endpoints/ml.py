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

clustering = SpatialClustering()

import os


from app.ai_model.yolo.config import BEST_MODEL_PATH

@router.get("/evaluation")
def ml_evaluation():
    yolo_trained = BEST_MODEL_PATH.exists()
    yolo_weights = str(BEST_MODEL_PATH)

    return {
        "yolo": {
            "trained": yolo_trained,
            "available": yolo_trained,
            "metrics": "evaluated" if yolo_trained else "unavailable"
        },
        "random_forest": {
            "trained": False,
            "available": False,
            "status": "not_trained",
            "metrics": "quarantined_pending_manual_training",
            "blocker": "Ontario dataset IRI regression ready for manual training. Production deployment requires genuine municipal road condition data."
        },
        "decision_tree": {
            "trained": False,
            "available": False,
            "status": "not_trained",
            "metrics": "quarantined_pending_manual_training",
            "blocker": "Ontario dataset IRI regression ready for manual training. Production deployment requires genuine municipal road condition data."
        },
        "logistic_regression": {
            "trained": False,
            "available": False,
            "status": "blocked",
            "metrics": "quarantined_invalid_synthetic_target",
            "blocker": "Synthetic 'Needs Maintenance' labels exhibit target leakage (deterministic threshold reproduction). Quarantined until authentic maintenance target data is procured."
        },
        "gradient_boosting": {
            "trained": False,
            "available": False,
            "status": "blocked",
            "metrics": "quarantined_invalid_synthetic_target",
            "blocker": "Synthetic 'Needs Maintenance' labels exhibit target leakage. Quarantined until authentic maintenance target data is procured."
        }
    }

@router.get("/models")
def ml_models():
    yolo_trained = BEST_MODEL_PATH.exists()
    yolo_weights = str(BEST_MODEL_PATH)

    return {
        "yolo": {
            "name": "YOLOv8 Detection",
            "trained": yolo_trained,
            "available": yolo_trained,
            "weights_path": yolo_weights if yolo_trained else None
        },

        "random_forest": {
            "name": "Random Forest Maintenance Prediction",
            "trained": False,
            "available": False,
            "status": "not_trained",
            "task": "Predict Roughness (IRI Regression)",
            "compatible_dataset": "ontario-pavement-2023",
            "weights_path": None
        },
        "decision_tree": {
            "name": "Decision Tree Maintenance Prediction",
            "trained": False,
            "available": False,
            "status": "not_trained",
            "task": "Predict Roughness (IRI Regression)",
            "compatible_dataset": "ontario-pavement-2023",
            "weights_path": None
        },
        "logistic_regression": {
            "name": "Logistic Regression Maintenance Prediction",
            "trained": False,
            "available": False,
            "status": "blocked",
            "task": "Predict Material Type (Classification)",
            "compatible_dataset": "ontario-pavement-2023",
            "weights_path": None
        },
        "gradient_boosting": {
            "name": "Gradient Boosting Maintenance Prediction",
            "trained": False,
            "available": False,
            "status": "blocked",
            "task": "Predict Overall Condition (PCI Regression)",
            "compatible_dataset": "ontario-pavement-2023",
            "weights_path": None
        }
    }

@router.get("/predictions/{issue_id}")
def ml_predictions(issue_id: int, db: Session = Depends(get_db)):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue: return {"error": "not found"}

    missing_features = ["PCI", "AADT", "Last Maintenance", "Average Rainfall", "Rutting", "IRI", "Road Type", "Asphalt Type"]
    missing_reason = f"Required road-context features are unavailable in issue records. Missing: {', '.join(missing_features)}."

    return {
        "yolo": {
            "status": "success" if issue.ai_confidence > 0 else "not_available"
        },
        "random_forest": {
            "status": "not_trained",
            "reason": f"Random Forest has not been manually trained on live features. {missing_reason}"
        },
        "decision_tree": {
            "status": "not_trained",
            "reason": f"Decision Tree has not been manually trained on live features. {missing_reason}"
        },
        "logistic_regression": {
            "status": "blocked",
            "reason": "Logistic Regression is quarantined due to synthetic label target leakage. Real municipal data required."
        },
        "gradient_boosting": {
            "status": "blocked",
            "reason": "Gradient Boosting is quarantined due to synthetic label target leakage. Real municipal data required."
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
            "id": "ontario-pavement-2023",
            "name": "Pavement Condition for Provincial Highways (2023)",
            "source": "Ontario Data Catalogue",
            "coverage": "Ontario, Canada",
            "license": "Open Government Licence - Ontario",
            "status": "DOWNLOADED_AND_VERIFIED",
            "is_synthetic": False,
            "row_count": 2132,
            "column_count": 12,
            "columns": ["SectionID", "Highway", "DIR", "FROM_Distance", "TO_Distance", "PCI", "DMI", "IRI", "Pave_Type", "Pavement_Section_From", "Pavement_Section_To", "FUNC_CLASS"],
            "target": "PCI, DMI, IRI, Pave_Type",
            "missing_values": "Low for key physical indices",
            "compatibility": "READY",
            "limitations": "International fallback used because Indian tabular datasets (e.g., NHAI, PWD) are strictly restricted or paywalled. Contains genuine physical condition measurements (DMI, IRI) supporting non-leaky regression and classification tasks.",
            "link": "https://data.ontario.ca/dataset/pavement-condition-for-provincial-highways"
        },
        {
            "id": "sf-pci-2023",
            "name": "San Francisco Pavement Condition Index (PCI) Scores",
            "source": "San Francisco Public Works / DataSF",
            "coverage": "San Francisco, CA, USA",
            "license": "Open Data (ODC-PDDL / Public Domain)",
            "status": "DOWNLOADED",
            "is_synthetic": False,
            "row_count": 19461,
            "column_count": 20,
            "columns": ["CNN", "Street_Name", "PCI_Score", "From_Street", "To_Street", "PCI_Change_Date", "Treatment_or_Survey", "Street_Accepted_For_Maintenance", "Functional_Class", "X", "Y", "Latitude", "Longitude", "Line", "Point", "Neighborhoods"],
            "target": "PCI_Score (Numeric 0-100)",
            "missing_values": "Low for key fields",
            "compatibility": "INCOMPATIBLE",
            "limitations": "Contains valid PCI target but strictly lacks required physical structural predictors (e.g., IRI, DMI, Rutting). Blocked to prevent memorizing coordinates instead of physical deterioration.",
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
            "limitations": "Upstream tabular models have not been trained yet. Generating synthetic downstream data requires genuine upstream predictions to avoid silent leakages.",
            "link": None
        }
    ]


@router.get("/lab/models")
def get_lab_models():
    # Return genuine status and correct non-leaky tasks
    return [
        {
            "id": "random_forest",
            "name": "Random Forest",
            "task": "Predict Roughness (Regression)",
            "compatible_dataset": "ontario-pavement-2023",
            "target_variable": "IRI (International Roughness Index)",
            "readiness": "READY_FOR_MANUAL_TRAINING",
            "training_status": "NOT_TRAINED",
            "dependency_status": "READY_FOR_TRAINING",
            "next_action": "Manual Training Required",
            "features": ["DMI", "Pave_Type", "FUNC_CLASS"],
            "preprocessing": "StandardScaler (DMI), OneHotEncoder (Pave_Type, FUNC_CLASS). MUST USE GroupShuffleSplit on 'Highway' to mitigate spatial target leakage, but unresolved overlap limitations exist."
        },
        {
            "id": "decision_tree",
            "name": "Decision Tree",
            "task": "Predict Roughness (Regression)",
            "compatible_dataset": "ontario-pavement-2023",
            "target_variable": "IRI (International Roughness Index)",
            "readiness": "READY_FOR_MANUAL_TRAINING",
            "training_status": "NOT_TRAINED",
            "dependency_status": "READY_FOR_TRAINING",
            "next_action": "Manual Training Required",
            "features": ["DMI", "Pave_Type", "FUNC_CLASS"],
            "preprocessing": "StandardScaler (DMI), OneHotEncoder (Pave_Type, FUNC_CLASS). MUST USE GroupShuffleSplit on 'Highway' to mitigate spatial target leakage, but unresolved overlap limitations exist."
        },
        {
            "id": "logistic_regression",
            "name": "Logistic Regression",
            "task": "Predict Material Type (Classification)",
            "compatible_dataset": "ontario-pavement-2023",
            "target_variable": "Pave_Type (AC vs CO vs PC vs ST)",
            "readiness": "BLOCKED_INVALID_TASK",
            "training_status": "NOT_TRAINED",
            "dependency_status": "BLOCKED_ON_TASK",
            "next_action": "Acquire classification dataset with genuine maintenance labels.",
            "features": ["IRI", "DMI", "FUNC_CLASS"],
            "preprocessing": "StandardScaler (IRI, DMI), OneHotEncoder (FUNC_CLASS)"
        },
        {
            "id": "gradient_boosting",
            "name": "Gradient Boosting",
            "task": "Predict Overall Condition (Regression)",
            "compatible_dataset": "ontario-pavement-2023",
            "target_variable": "PCI (Pavement Condition Index)",
            "readiness": "BLOCKED_INVALID_TASK",
            "training_status": "NOT_TRAINED",
            "dependency_status": "BLOCKED_ON_TASK",
            "next_action": "Acquire dataset with genuine physical predictors for PCI (like Traffic/AADT or Age).",
            "features": ["Pave_Type", "FUNC_CLASS", "DIR", "Segment_Length"],
            "preprocessing": "Feature Engineering (TO_Distance - FROM_Distance), OneHotEncoder (Categoricals). Note: DMI and IRI are strictly excluded to prevent target leakage."
        }
    ]



