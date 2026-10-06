import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
DATASET_YAML = BASE_DIR / 'datasets' / 'RDD2020' / 'data.yaml'
MODEL_NAME = 'yolov8n.pt'
IMG_SIZE = 640
EPOCHS = 50
BATCH_SIZE = 16
ARTIFACT_DIR = Path(__file__).resolve().parent / 'weights'
BEST_MODEL_PATH = ARTIFACT_DIR / 'best.pt'
CLASS_NAMES = ['D00', 'D10', 'D20', 'D40']
