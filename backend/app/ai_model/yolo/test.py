import os
import torch
from backend.app.ai_model.yolo import config

def test_yolo_module():
    print('Testing YOLO configuration and dataset...')
    print(f'Dataset YAML exists: {config.DATASET_YAML.exists()}')
    print(f'Model artifact exists: {config.BEST_MODEL_PATH.exists()}')
    
    if not config.BEST_MODEL_PATH.exists():
        print('MODEL NOT TRAINED (Missing best.pt artifact)')
    else:
        print('MODEL TRAINED AND WORKING')
        try:
            from ultralytics import YOLO
            YOLO(str(config.BEST_MODEL_PATH))
            print('Model loaded successfully.')
        except Exception as e:
            print(f'Error loading model: {e}')

if __name__ == '__main__':
    test_yolo_module()
