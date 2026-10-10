import os
from pathlib import Path

# Project root path resolution
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
DATASET_PATH = BASE_DIR / "datasets" / "priority" / "ESC 12 Pavement Dataset.csv"

WEIGHTS_DIR = Path(__file__).resolve().parent / "weights"
MODEL_OUTPUT_PATH = WEIGHTS_DIR / "decision_tree.joblib"
METADATA_PATH = WEIGHTS_DIR / "model_metadata.json"
FEATURE_IMPORTANCE_PATH = WEIGHTS_DIR / "feature_importance.csv"

RANDOM_STATE = 42
TEST_SIZE = 0.20
MAX_DEPTH = 10
MIN_SAMPLES_SPLIT = 10
MIN_SAMPLES_LEAF = 4

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
