import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
DATASET_PATH = BASE_DIR / "datasets" / "priority" / "ESC 12 Pavement Dataset.csv"

WEIGHTS_DIR = Path(__file__).resolve().parent / "weights"
MODEL_OUTPUT_PATH = WEIGHTS_DIR / "logistic_regression.joblib"
METADATA_PATH = WEIGHTS_DIR / "model_metadata.json"
COEFFICIENTS_PATH = WEIGHTS_DIR / "coefficients.csv"

RANDOM_STATE = 42
TEST_SIZE = 0.20
MAX_ITER = 1000
C_VALUE = 1.0

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
