import pandas as pd
import joblib
from backend.app.ai_model.random_forest.config import MODEL_OUTPUT_PATH, NUMERIC_FEATURES, CATEGORICAL_FEATURES

def predict(features: dict):
    if not MODEL_OUTPUT_PATH.exists():
        return {
            "status": "not_available",
            "reason": "Random Forest model artifact not found."
        }

    try:
        pipeline = joblib.load(MODEL_OUTPUT_PATH)
        
        # Convert dictionary to DataFrame
        df = pd.DataFrame([features])
        
        # Validate that all required features are present
        required_features = NUMERIC_FEATURES + CATEGORICAL_FEATURES
        missing_features = [f for f in required_features if f not in df.columns]
        if missing_features:
            return {
                "status": "error",
                "reason": f"Missing features: {missing_features}"
            }
            
        # Ensure only the required features are used and in correct order
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


if __name__ == "__main__":
    import json
    # A single sample purely for CLI testing
    sample_features = {
        "PCI": 65.0,
        "AADT": 15000,
        "Last Maintenance": 2.5,
        "Average Rainfall": 120.5,
        "Rutting": 5.2,
        "IRI": 2.1,
        "Road Type": "Arterial",
        "Asphalt Type": "HMA"
    }
    print(f"Running prediction on sample:\n{json.dumps(sample_features, indent=2)}")
    
    result = predict(sample_features)
    print(f"\nResult:\n{json.dumps(result, indent=2)}")
