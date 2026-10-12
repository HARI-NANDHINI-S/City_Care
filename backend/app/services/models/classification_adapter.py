from typing import Dict, Any, List, Optional
from pathlib import Path
import time
from app.services.models.base_adapter import BaseDefectModelAdapter

class IRDIDClassificationAdapter(BaseDefectModelAdapter):
    """
    Adapter for candidate IRDID whole-image classification model.
    Designed for:
      - Damaged Road Surface (broken_edges)
      - Waterlogging (waterlogged_roads)
    Operates exclusively in whole-image scene classification mode (no bounding boxes).
    Truthfully reports 'unsupported' when weights are not present.
    """

    CLASS_MAPPING = {
        "broken_edges": "Damaged Road Surface",
        "waterlogged_roads": "Waterlogging",
        "Damaged Road Surface": "Damaged Road Surface",
        "Waterlogging": "Waterlogging",
    }

    def __init__(self, weights_path: Optional[Path] = None):
        if weights_path is not None:
            self._weights_path = Path(weights_path)
        else:
            self._weights_path = Path(__file__).resolve().parent.parent / "weights" / "irdid_classifier.pt"
        self._model = None
        self._load_error = None
        self._is_loaded = False

    @property
    def model_id(self) -> str:
        return "irdid-classifier-candidate"

    @property
    def supported_categories(self) -> List[str]:
        return ["Damaged Road Surface", "Waterlogging"]

    @property
    def is_available(self) -> bool:
        if not self._weights_path or not self._weights_path.exists():
            return False
        if not self._is_loaded and not self._load_error:
            self._lazy_load()
        return self._is_loaded

    def _lazy_load(self):
        if not self._weights_path or not self._weights_path.exists():
            self._load_error = f"Classification weights not found at {self._weights_path}"
            return
        try:
            from ultralytics import YOLO
            self._model = YOLO(str(self._weights_path))
            self._is_loaded = True
        except Exception as e:
            self._load_error = f"Failed to load classification model: {e}"

    def infer(self, image_path: str) -> Dict[str, Any]:
        if not self.is_available:
            return {
                "status": "unsupported",
                "model_id": self.model_id,
                "raw_detections": [],
                "execution_time_ms": 0.0,
                "error_message": f"IRDID classifier weights not found at {self._weights_path}. Candidate model is pending manual training on curated IRDID dataset."
            }

        start_time = time.time()
        try:
            results = self._model(image_path)
            detections = []
            for result in results:
                if hasattr(result, "probs") and result.probs is not None:
                    top_idx = int(result.probs.top1)
                    conf = float(result.probs.top1conf.item())
                    raw_name = result.names[top_idx]
                    mapped_name = self.CLASS_MAPPING.get(raw_name, raw_name)
                    if mapped_name in self.supported_categories:
                        detections.append({
                            "class": mapped_name,
                            "raw_class": raw_name,
                            "confidence": conf,
                            "bounding_box": None  # Genuine classification without bounding box
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
