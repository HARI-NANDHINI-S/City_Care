import os
from app.ai_model.yolo import config

class YOLOPredictor:
    def __init__(self):
        self.model = None
        self.is_loaded = False
        self.load_error = None
        
        if config.BEST_MODEL_PATH.exists():
            try:
                from ultralytics import YOLO
                self.model = YOLO(str(config.BEST_MODEL_PATH))
                self.is_loaded = True
            except ImportError as ie:
                self.load_error = f"Ultralytics/PyTorch dependency unavailable: {ie}"
            except OSError as oe:
                self.load_error = f"Host OS security/DLL policy prevented loading vision engine: {oe}"
            except Exception as e:
                self.load_error = f"Failed to initialize YOLO model: {e}"
        else:
            self.load_error = "Model weights artifact best.pt not found."
                
    def predict(self, image_path):
        if not self.is_loaded:
            return {
                'status': 'error',
                'reason': self.load_error or 'Model artifact best.pt not found or failed to load.'
            }
            
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
