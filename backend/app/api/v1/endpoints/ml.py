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
    df = generate_synthetic_priority_dataset(100)
    models = CivicVisionPriorityModels()
    results = models.train_and_evaluate(df)
    return results

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
    
    features = {
        'issue_count': 1, 'damage_area': 0.1, 'detection_confidence': issue.ai_confidence or 0.8, 'severity': getattr(issue.severity, 'value', 1) if issue.severity else 1,
        'road_age_years': 5, 'road_condition': 1, 'traffic_volume': 1000, 'accident_history': 0,
        'nearby_school': 0, 'nearby_hospital': 0, 'drainage_condition': 1, 'days_since_maintenance': 365
    }
    
    models = CivicVisionPriorityModels()
    pred = models.predict_priority(features)
    
    from app.ml.recommendation import get_maintenance_recommendation
    rec = get_maintenance_recommendation(pred["priority_class"], issue.issue_type.value if issue.issue_type else "Pothole", features)
    
    return {
        "prediction": pred,
        "recommendation": rec
    }

@router.get("/explanations/{issue_id}")
def ml_explanations(issue_id: int, db: Session = Depends(get_db)):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue: return {"error": "not found"}
    
    features = {
        'issue_count': 1, 'damage_area': 0.1, 'detection_confidence': issue.ai_confidence or 0.8, 'severity': getattr(issue.severity, 'value', 1) if issue.severity else 1,
        'road_age_years': 5, 'road_condition': 1, 'traffic_volume': 1000, 'accident_history': 0,
        'nearby_school': 0, 'nearby_hospital': 0, 'drainage_condition': 1, 'days_since_maintenance': 365
    }
    
    explainer = ShapExplainer()
    res = explainer.explain_prediction(features)
    return res

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
