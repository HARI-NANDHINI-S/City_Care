import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
DATASET_PATH = BASE_DIR / "datasets" / "priority" / "ESC 12 Pavement Dataset.csv"

WEIGHTS_DIR = Path(__file__).resolve().parent / "weights"
MODEL_OUTPUT_PATH = WEIGHTS_DIR / "gradient_boosting.joblib"
METADATA_PATH = WEIGHTS_DIR / "model_metadata.json"
FEATURE_IMPORTANCE_PATH = WEIGHTS_DIR / "feature_importance.csv"

RANDOM_STATE = 42
TEST_SIZE = 0.20
N_ESTIMATORS = 100
LEARNING_RATE = 0.1
MAX_DEPTH = 5

NUMERIC_FEATURES = [
    "PCI",
    "AADT",
    "Last Maintenance",
    "Average Rainfall",
    "Rutting",
    "IRI"
]

CATEGORICAL_FEATURES = [
    "Road Type",
    "Asphalt Type"
]

TARGET_COLUMN = "Needs Maintenance"
