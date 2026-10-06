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

@router.get("/evaluation")
def ml_evaluation():
    return {
        "status": "not_available",
        "reason": "Priority ML training is blocked by the missing real dataset. No evaluation metrics available."
    }

@router.get("/models")
def ml_models():
    return {
        "models": [
            "Decision Tree", "Logistic Regression", "Random Forest", "Gradient Boosting"
        ],
        "primary": "Random Forest",
        "baselines": ["Decision Tree", "Logistic Regression"],
        "comparison": ["Gradient Boosting"]
    }

@router.get("/predictions/{issue_id}")
def ml_predictions(issue_id: int, db: Session = Depends(get_db)):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue: return {"error": "not found"}
    
    models = CivicVisionPriorityModels()
    model, scaler = models.get_primary_model()
    if not model:
        return {
            "status": "not_available",
            "reason": "Priority ML model is not trained yet due to missing dataset."
        }
    
    # We would build real features here, but since the model isn't trained and we have no real context features in DB, we fail explicitly
    return {
        "status": "not_available",
        "reason": "Real contextual features (traffic, road age, etc.) are missing from the current database schema."
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
    clustering = SpatialClustering()
    res = clustering.cluster_issues(issues_list)
    return res
