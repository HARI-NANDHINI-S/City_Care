import os
import sys
import unittest
import pandas as pd

# Add backend directory to sys.path if not present
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from app.ai_model.decision_tree.config import DATASET_PATH, MODEL_OUTPUT_PATH, NUMERIC_FEATURES, CATEGORICAL_FEATURES, TARGET_COLUMN
from app.ai_model.decision_tree.predict import predict, is_valid_ontario_artifact

class TestDecisionTreeModule(unittest.TestCase):
    
    def test_01_ontario_dataset_exists(self):
        self.assertTrue(DATASET_PATH.exists(), f"Ontario dataset not found at {DATASET_PATH}")
        
    def test_02_required_ontario_columns_exist(self):
        if not DATASET_PATH.exists():
            self.skipTest("Ontario dataset missing")
            
        df = pd.read_csv(DATASET_PATH, nrows=5)
        df.columns = df.columns.str.strip()
        required_columns = NUMERIC_FEATURES + CATEGORICAL_FEATURES + [TARGET_COLUMN]
        missing_cols = [col for col in required_columns if col not in df.columns]
        self.assertEqual(len(missing_cols), 0, f"Missing columns in Ontario dataset: {missing_cols}")
        
    def test_03_legacy_artifact_quarantined(self):
        valid, reason = is_valid_ontario_artifact()
        self.assertFalse(valid, "Legacy artifact must not be validated as a genuine Ontario IRI model")
        self.assertIn("quarantined", reason.lower())
        
    def test_04_predict_reports_not_available_on_legacy_artifact(self):
        sample_features = {
            "DMI": 5.2,
            "Pave_Type": "AC",
            "FUNC_CLASS": "Freeway"
        }
        res = predict(sample_features)
        self.assertEqual(res.get("status"), "not_available")
        self.assertIn("quarantined", res.get("reason", "").lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
