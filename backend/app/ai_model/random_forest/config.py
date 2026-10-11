import os
from pathlib import Path

# Project root path resolution
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
DATASET_PATH = BASE_DIR / "datasets" / "priority" / "international_road_condition" / "raw" / "ontario_2023_pavement.csv"
LEGACY_DATASET_PATH = BASE_DIR / "datasets" / "priority" / "ESC 12 Pavement Dataset.csv"

WEIGHTS_DIR = Path(__file__).resolve().parent / "weights"
MODEL_OUTPUT_PATH = WEIGHTS_DIR / "random_forest.joblib"
METADATA_PATH = WEIGHTS_DIR / "model_metadata.json"
FEATURE_IMPORTANCE_PATH = WEIGHTS_DIR / "feature_importance.csv"

RANDOM_STATE = 42
TEST_SIZE = 0.20
N_ESTIMATORS = 100
MAX_DEPTH = None

# Valid Ontario Roughness (IRI) Prediction Features
NUMERIC_FEATURES = [
    "DMI"
]

CATEGORICAL_FEATURES = [
    "Pave_Type",
    "FUNC_CLASS"
]

TARGET_COLUMN = "IRI"

# Legacy features for quarantine recognition
LEGACY_NUMERIC_FEATURES = ["PCI", "AADT", "Last Maintenance", "Average Rainfall", "Rutting", "IRI"]
LEGACY_CATEGORICAL_FEATURES = ["Road Type", "Asphalt Type"]
LEGACY_TARGET_COLUMN = "Needs Maintenance"
