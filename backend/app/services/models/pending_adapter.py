import os
from typing import Dict, Any, List
from pathlib import Path
from app.services.models.base_adapter import BaseDefectModelAdapter

class PendingModelAdapter(BaseDefectModelAdapter):
    """
    Adapter for categories that have data specifications or are pending manual model training.
    Does NOT fabricate detections. Truthfully reports status and informs user.
    """

    def __init__(self, model_id: str, supported_categories: List[str], blocker_reason: str, weights_path: Path = None):
        self._model_id = model_id
        self._supported_categories = supported_categories
        self._blocker_reason = blocker_reason
        self._weights_path = weights_path

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def supported_categories(self) -> List[str]:
        return self._supported_categories

    @property
    def is_available(self) -> bool:
        if self._weights_path and self._weights_path.exists():
            return True
        return False

    def infer(self, image_path: str) -> Dict[str, Any]:
        return {
            "status": "unsupported",
            "model_id": self.model_id,
            "raw_detections": [],
            "execution_time_ms": 0.0,
            "error_message": self._blocker_reason
        }
