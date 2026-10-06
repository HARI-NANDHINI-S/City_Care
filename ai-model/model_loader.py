import os
from typing import Dict, Any, List

class CivicVisionModelLoader:
    def __init__(self, weights_path: str = "backend/app/services/weights/best.pt"):
        self.weights_path = weights_path
        self.model = None
        self.is_loaded = False
        self._initialize_model()

    def _initialize_model(self):
        if os.path.exists(self.weights_path):
            try:
                from ultralytics import YOLO
                self.model = YOLO(self.weights_path)
                self.is_loaded = True
                print(f"[OK] Successfully loaded custom YOLO model weights from {self.weights_path}")
            except Exception as e:
                print(f"[WARNING] Failed to load custom PyTorch weights ({e}). Defaulting to CivicVision Vision Engine.")
        else:
            print(f"[INFO] No custom PyTorch weights found at {self.weights_path}. Running with CivicVision Vision Engine.")

    def predict(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Runs object detection inference on an input image.
        Returns list of bounding box dicts.
        """
        if self.is_loaded and self.model is not None:
            results = self.model(image_path)
            boxes_data = []
            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    cls_name = self.model.names.get(cls_id, "Defect")
                    conf = float(box.conf[0])
                    xywh = box.xywh[0].tolist()
                    boxes_data.append({
                        "class": cls_name,
                        "confidence": round(conf, 2),
                        "x": int(xywh[0]),
                        "y": int(xywh[1]),
                        "width": int(xywh[2]),
                        "height": int(xywh[3])
                    })
            return boxes_data
        else:
            raise Exception("Model weights not available. Object detection model is not trained yet.")
