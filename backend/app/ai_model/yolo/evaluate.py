import os
from ultralytics import YOLO
from backend.app.ai_model.yolo import config

def evaluate():
    if not config.BEST_MODEL_PATH.exists():
        print('[ERROR] Model artifact best.pt not found. Cannot evaluate.')
        return
        
    print('Evaluating YOLO model on test split...')
    model = YOLO(str(config.BEST_MODEL_PATH))
    
    metrics = model.val(data=str(config.DATASET_YAML), split='test')
    
    print('Evaluation Results:')
    print(f'mAP50-95: {metrics.box.map}')
    print(f'mAP50: {metrics.box.map50}')
    print(f'Precision: {metrics.box.mp}')
    print(f'Recall: {metrics.box.mr}')
    print('D10 class has only 68 annotations, performance may be skewed.')
    
if __name__ == '__main__':
    evaluate()
