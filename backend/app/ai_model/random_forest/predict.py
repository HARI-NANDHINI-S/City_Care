import json
import pandas as pd
import joblib
from app.ai_model.random_forest.config import (
    MODEL_OUTPUT_PATH,
    METADATA_PATH,
    NUMERIC_FEATURES,
    CATEGORICAL_FEATURES,
    TARGET_COLUMN
)

def is_valid_ontario_artifact() -> tuple[bool, str]:
    """
    Verifies that the serialized artifact and metadata correspond to the valid
    Ontario IRI regression task, rather than legacy synthetic ESC 12 classification.
    """
    if not MODEL_OUTPUT_PATH.exists():
        return False, "Model artifact file not found."
    if not METADATA_PATH.exists():
        return False, "Model metadata file not found."
    
    try:
        with open(METADATA_PATH, "r") as f:
            metadata = json.load(f)
            
        target = metadata.get("target")
        if target != TARGET_COLUMN:
            return False, f"Artifact quarantined: metadata target is '{target}', expected '{TARGET_COLUMN}' (Ontario IRI regression)."
            
        dataset = metadata.get("dataset", metadata.get("dataset_filename", ""))
        if "ESC 12" in dataset:
            return False, "Artifact quarantined: derived from legacy synthetic ESC 12 dataset."
            
        return True, "Valid Ontario artifact verified."
    except Exception as e:
        return False, f"Failed to validate metadata: {str(e)}"

def predict(features: dict):
    valid, reason = is_valid_ontario_artifact()
    if not valid:
        return {
            "status": "not_available",
            "reason": f"Random Forest valid artifact not available. {reason}"
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
        
        return {
            "status": "success",
            "prediction": float(prediction_val),
            "target": TARGET_COLUMN,
            "unit": "m/km"
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
