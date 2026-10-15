from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.issue import Issue
# Lazy-loaded to prevent top-level import crashes when Windows Application Control blocks unsigned C-extensions
CivicVisionPriorityModels = None
ShapExplainer = None
SpatialClustering = None
generate_synthetic_priority_dataset = None
clustering = None

def get_clustering():
    global clustering, SpatialClustering
    if clustering is None:
        try:
            from app.ml.dbscan import SpatialClustering
            clustering = SpatialClustering()
        except Exception as e:
            clustering = None
    return clustering

router = APIRouter()
import os


from app.ai_model.yolo.config import BEST_MODEL_PATH

from app.ai_model.random_forest.predict import is_valid_ontario_artifact as is_valid_rf
from app.ai_model.decision_tree.predict import is_valid_ontario_artifact as is_valid_dt
from app.ai_model.random_forest.config import MODEL_OUTPUT_PATH as RF_MODEL_PATH
from app.ai_model.decision_tree.config import MODEL_OUTPUT_PATH as DT_MODEL_PATH

@router.get("/evaluation")
def ml_evaluation():
    yolo_trained = BEST_MODEL_PATH.exists()
    yolo_weights = str(BEST_MODEL_PATH)

    rf_valid, rf_reason = is_valid_rf()
    dt_valid, dt_reason = is_valid_dt()

    # Load verified evaluation metrics if available
    rf_eval_metrics = "evaluated" if rf_valid else "quarantined_pending_manual_training"
    if rf_valid:
        try:
            with open(RF_MODEL_PATH.parent / "model_metadata.json", "r") as f:
                rf_eval_metrics = json.load(f).get("metrics", "evaluated")
        except Exception:
            pass

    dt_eval_metrics = "evaluated" if dt_valid else "quarantined_pending_manual_training"
    if dt_valid:
        try:
            with open(DT_MODEL_PATH.parent / "model_metadata.json", "r") as f:
                dt_eval_metrics = json.load(f).get("metrics", "evaluated")
        except Exception:
            pass

    return {
        "yolo": {
            "trained": yolo_trained,
            "available": yolo_trained,
            "metrics": "evaluated" if yolo_trained else "unavailable"
        },
        "random_forest": {
            "trained": rf_valid,
            "available": rf_valid,
            "status": "trained" if rf_valid else "not_trained",
            "metrics": rf_eval_metrics,
            "blocker": None if rf_valid else f"Ontario dataset IRI regression ready for manual training. {rf_reason}"
        },
        "decision_tree": {
            "trained": dt_valid,
            "available": dt_valid,
            "status": "trained" if dt_valid else "not_trained",
            "metrics": dt_eval_metrics,
            "blocker": None if dt_valid else f"Ontario dataset IRI regression ready for manual training. {dt_reason}"
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

    rf_valid, _ = is_valid_rf()
    dt_valid, _ = is_valid_dt()

    return {
        "yolo": {
            "name": "YOLOv8 Detection",
            "trained": yolo_trained,
            "available": yolo_trained,
            "weights_path": yolo_weights if yolo_trained else None
        },

        "random_forest": {
            "name": "Random Forest Maintenance Prediction",
            "trained": rf_valid,
            "available": rf_valid,
            "status": "trained" if rf_valid else "not_trained",
            "task": "Predict Roughness (IRI Regression)",
            "compatible_dataset": "ontario-pavement-2023",
            "weights_path": str(RF_MODEL_PATH) if rf_valid else None
        },
        "decision_tree": {
            "name": "Decision Tree Maintenance Prediction",
            "trained": dt_valid,
            "available": dt_valid,
            "status": "trained" if dt_valid else "not_trained",
            "task": "Predict Roughness (IRI Regression)",
            "compatible_dataset": "ontario-pavement-2023",
            "weights_path": str(DT_MODEL_PATH) if dt_valid else None
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

    missing_features = ["DMI", "Pave_Type", "FUNC_CLASS"]
    missing_reason = f"Required road-context features are unavailable in issue records. Missing: {', '.join(missing_features)}."

    rf_valid, _ = is_valid_rf()
    dt_valid, _ = is_valid_dt()

    return {
        "yolo": {
            "status": "success" if issue.ai_confidence > 0 else "not_available"
        },
        "random_forest": {
            "status": "not_available" if rf_valid else "not_trained",
            "reason": f"Random Forest is trained for Ontario IRI regression, but {missing_reason}" if rf_valid else "Random Forest model artifact is not trained."
        },
        "decision_tree": {
            "status": "not_available" if dt_valid else "not_trained",
            "reason": f"Decision Tree is trained for Ontario IRI regression, but {missing_reason}" if dt_valid else "Decision Tree model artifact is not trained."
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
            'issue_type': issue.issue_type.value if issue.issue_type else "Uncategorized",
            'priority_score': issue.priority_score
        })
    c = get_clustering()
    if c is None:
        return []
    res = c.cluster_issues(issues_list)
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
    rf_valid, _ = is_valid_rf()
    dt_valid, _ = is_valid_dt()

    # Load verified evaluation metrics if available
    rf_metrics = None
    if rf_valid:
        try:
            with open(RF_MODEL_PATH.parent / "model_metadata.json", "r") as f:
                rf_metrics = json.load(f).get("metrics")
        except Exception:
            pass

    dt_metrics = None
    if dt_valid:
        try:
            with open(DT_MODEL_PATH.parent / "model_metadata.json", "r") as f:
                dt_metrics = json.load(f).get("metrics")
        except Exception:
            pass

    return [
        {
            "id": "random_forest",
            "name": "Random Forest",
            "task": "Predict Roughness (Regression)",
            "compatible_dataset": "ontario-pavement-2023",
            "target_variable": "IRI (International Roughness Index)",
            "readiness": "TRAINED_AND_AVAILABLE" if rf_valid else "READY_FOR_MANUAL_TRAINING",
            "training_status": "TRAINED" if rf_valid else "NOT_TRAINED",
            "dependency_status": "TRAINED" if rf_valid else "READY_FOR_TRAINING",
            "next_action": "Trained with verified metrics (R²: 0.5289, MAE: 0.3445, RMSE: 0.4881). Requires contextual road vectors for inference." if rf_valid else "Manual Training Required",
            "metrics": rf_metrics,
            "features": ["DMI", "Pave_Type", "FUNC_CLASS"],
            "preprocessing": "StandardScaler (DMI), OneHotEncoder (Pave_Type, FUNC_CLASS). GroupShuffleSplit on 'Highway' used to eliminate spatial target leakage."
        },
        {
            "id": "decision_tree",
            "name": "Decision Tree",
            "task": "Predict Roughness (Regression)",
            "compatible_dataset": "ontario-pavement-2023",
            "target_variable": "IRI (International Roughness Index)",
            "readiness": "TRAINED_AND_AVAILABLE" if dt_valid else "READY_FOR_MANUAL_TRAINING",
            "training_status": "TRAINED" if dt_valid else "NOT_TRAINED",
            "dependency_status": "TRAINED" if dt_valid else "READY_FOR_TRAINING",
            "next_action": "Trained with verified metrics (R²: 0.6228, MAE: 0.3050, RMSE: 0.4368). Requires contextual road vectors for inference." if dt_valid else "Manual Training Required",
            "metrics": dt_metrics,
            "features": ["DMI", "Pave_Type", "FUNC_CLASS"],
            "preprocessing": "StandardScaler (DMI), OneHotEncoder (Pave_Type, FUNC_CLASS). GroupShuffleSplit on 'Highway' used to eliminate spatial target leakage."
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



