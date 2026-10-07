import unittest
import pandas as pd
from backend.app.ai_model.random_forest.config import DATASET_PATH, MODEL_OUTPUT_PATH, NUMERIC_FEATURES, CATEGORICAL_FEATURES, TARGET_COLUMN
from backend.app.ai_model.random_forest.predict import predict

class TestRandomForestModule(unittest.TestCase):
    
    def test_01_dataset_exists(self):
        self.assertTrue(DATASET_PATH.exists(), f"Dataset not found at {DATASET_PATH}")
        
    def test_02_required_columns_exist(self):
        if not DATASET_PATH.exists():
            self.skipTest("Dataset missing")
            
        df = pd.read_csv(DATASET_PATH, nrows=5)
        required_columns = NUMERIC_FEATURES + CATEGORICAL_FEATURES + [TARGET_COLUMN]
        missing_cols = [col for col in required_columns if col not in df.columns]
        self.assertEqual(len(missing_cols), 0, f"Missing columns in dataset: {missing_cols}")
        
    def test_03_saved_model_exists(self):
        if not MODEL_OUTPUT_PATH.exists():
            self.fail(f"Model artifact not found at {MODEL_OUTPUT_PATH}. Please run training first.")
        self.assertTrue(MODEL_OUTPUT_PATH.exists())
        
    def test_04_model_loads_successfully(self):
        if not MODEL_OUTPUT_PATH.exists():
            self.skipTest("Model missing")
            
        import joblib
        try:
            pipeline = joblib.load(MODEL_OUTPUT_PATH)
            self.assertIsNotNone(pipeline)
        except Exception as e:
            self.fail(f"Failed to load model: {e}")
            
    def test_05_prediction_structure_and_values(self):
        if not MODEL_OUTPUT_PATH.exists():
            self.skipTest("Model missing")
            
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
        
        result = predict(sample_features)
        
        self.assertEqual(result.get("status"), "success")
        self.assertIn("prediction", result)
        self.assertIn("label", result)
        self.assertIn("probability", result)
        
        self.assertIn(result["prediction"], [0, 1])
        self.assertIn(result["label"], ["NO_MAINTENANCE", "MAINTENANCE_REQUIRED"])
        self.assertTrue(0.0 <= result["probability"] <= 1.0)
        
    def test_06_missing_context(self):
        if not MODEL_OUTPUT_PATH.exists():
            self.skipTest("Model missing")
            
        incomplete_features = {
            "PCI": 65.0,
            # Missing AADT, etc.
        }
        
        result = predict(incomplete_features)
        
        self.assertEqual(result.get("status"), "error")
        self.assertIn("Missing features", result.get("reason", ""))


if __name__ == '__main__':
    unittest.main(verbosity=2)
