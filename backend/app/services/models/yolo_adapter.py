import os
import time
from typing import Dict, Any, List
from pathlib import Path

from app.services.models.base_adapter import BaseDefectModelAdapter
from app.ai_model.yolo import config

class YOLOv8RoadDamageAdapter(BaseDefectModelAdapter):
    """
    Adapter for existing YOLOv8 Road Damage model trained on Indian RDD2020/RDD2022 data.
    Detects:
      - D00 -> Longitudinal Crack
      - D10 -> Transverse Crack
      - D20 -> Alligator Crack
      - D40 -> Pothole
    """

    CLASS_MAPPING = {
        "D00": "Longitudinal Crack",
        "D10": "Transverse Crack",
        "D20": "Alligator Crack",
        "D40": "Pothole",
        # Support if model outputs name directly:
        "pothole": "Pothole",
        "longitudinal_crack": "Longitudinal Crack",
        "transverse_crack": "Transverse Crack",
        "alligator_crack": "Alligator Crack",
    }

    def __init__(self, weights_path: Path = None):
        self._weights_path = weights_path or config.BEST_MODEL_PATH
        self._model = None
        self._load_error = None
        self._is_loaded = False

    @property
    def model_id(self) -> str:
        return "yolov8-rdd2020-india-v1"

    @property
    def supported_categories(self) -> List[str]:
        return ["Pothole", "Longitudinal Crack", "Transverse Crack", "Alligator Crack"]

    @property
    def is_available(self) -> bool:
        if not self._is_loaded and not self._load_error:
            self._lazy_load()
        return self._is_loaded

    def _lazy_load(self):
        if not self._weights_path.exists():
            self._load_error = f"Model weights not found at {self._weights_path}"
            return

        try:
            from ultralytics import YOLO
            self._model = YOLO(str(self._weights_path))
            self._is_loaded = True
        except Exception as e:
            self._load_error = f"Failed to initialize Ultralytics YOLO: {e}"

    def infer(self, image_path: str) -> Dict[str, Any]:
        if not self.is_available:
            return {
                "status": "error",
                "model_id": self.model_id,
                "raw_detections": [],
                "execution_time_ms": 0.0,
                "error_message": self._load_error or "Model weights not available"
            }

        start_time = time.time()
        try:
            results = self._model(image_path)
            detections = []
            for result in results:
                for box in result.boxes:
                    cls_idx = int(box.cls[0].item())
                    conf = float(box.conf[0].item())
                    coords = box.xyxy[0].tolist()

                    raw_name = config.CLASS_NAMES[cls_idx] if cls_idx < len(config.CLASS_NAMES) else str(cls_idx)
                    mapped_name = self.CLASS_MAPPING.get(raw_name, raw_name)

                    detections.append({
                        "class": mapped_name,
                        "raw_class": raw_name,
                        "confidence": conf,
                        "bounding_box": coords
                    })

            exec_time = (time.time() - start_time) * 1000.0
            return {
                "status": "success",
                "model_id": self.model_id,
                "raw_detections": detections,
                "execution_time_ms": round(exec_time, 2),
                "error_message": None
            }
        except Exception as e:
            exec_time = (time.time() - start_time) * 1000.0
            return {
                "status": "error",
                "model_id": self.model_id,
                "raw_detections": [],
                "execution_time_ms": round(exec_time, 2),
                "error_message": str(e)
            }
