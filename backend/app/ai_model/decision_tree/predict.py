import pandas as pd
import joblib
from app.ai_model.decision_tree.config import MODEL_OUTPUT_PATH, NUMERIC_FEATURES, CATEGORICAL_FEATURES

def predict(features: dict):
    if not MODEL_OUTPUT_PATH.exists():
        return {
            "status": "not_available",
            "reason": "Decision Tree model artifact not found."
        }

    try:
        pipeline = joblib.load(MODEL_OUTPUT_PATH)
        
        df = pd.DataFrame([features])
        
        required_features = NUMERIC_FEATURES + CATEGORICAL_FEATURES
        missing_features = [f for f in required_features if f not in df.columns]
        if missing_features:
            return {
                "status": "error",
                "reason": f"Missing features: {missing_features}"
            }
            
        X = df[required_features]
        
        prediction_val = pipeline.predict(X)[0]
        prediction_prob = pipeline.predict_proba(X)[0]
        
        probability = float(prediction_prob[1] if prediction_val == 1 else prediction_prob[0])
        
        return {
            "status": "success",
            "prediction": int(prediction_val),
            "label": "MAINTENANCE_REQUIRED" if prediction_val == 1 else "NO_MAINTENANCE",
            "probability": probability
        }

    except Exception as e:
        return {
            "status": "error",
            "reason": str(e)
        }
