import os
from ultralytics import YOLO
from backend.app.ai_model.yolo import config

class YOLOPredictor:
    def __init__(self):
        self.model = None
        self.is_loaded = False
        
        if config.BEST_MODEL_PATH.exists():
            try:
                self.model = YOLO(str(config.BEST_MODEL_PATH))
                self.is_loaded = True
            except Exception as e:
                print(f'Error loading model: {e}')
                
    def predict(self, image_path):
        if not self.is_loaded:
            return {'status': 'error', 'reason': 'Model artifact best.pt not found or failed to load.'}
            
        results = self.model(image_path)
        detections = []
        for result in results:
            for box in result.boxes:
                cls_idx = int(box.cls[0].item())
                confidence = float(box.conf[0].item())
                coords = box.xyxy[0].tolist()
                class_name = config.CLASS_NAMES[cls_idx] if cls_idx < len(config.CLASS_NAMES) else str(cls_idx)
                
                detections.append({
                    'class': class_name,
                    'confidence': confidence,
                    'bounding_box': coords
                })
                
        return {
            'status': 'success',
            'detections': detections,
            'count': len(detections)
        }

predictor_instance = None
def predict(image_path):
    global predictor_instance
    if predictor_instance is None:
        predictor_instance = YOLOPredictor()
    return predictor_instance.predict(image_path)
