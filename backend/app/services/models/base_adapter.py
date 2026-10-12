from abc import ABC, abstractmethod
from typing import Dict, Any, List
import time
import os

class BaseDefectModelAdapter(ABC):
    """
    Abstract base class for all vision defect adapters.
    Ensures modular, decoupled architecture where models can be added, updated, or tested independently.
    """

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Unique model identifier and version (e.g., yolov8-rdd2020-india-v1)."""
        pass

    @property
    @abstractmethod
    def supported_categories(self) -> List[str]:
        """List of standard defect category names predicted by this model."""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the model weights exist and the engine can execute."""
        pass

    @abstractmethod
    def infer(self, image_path: str) -> Dict[str, Any]:
        """
        Executes model inference on image and returns normalized detection list:
        {
            "status": "success" | "error" | "unsupported",
            "model_id": str,
            "raw_detections": [
                {
                    "class": str, # Mapped standard category name
                    "raw_class": str, # Original model output class name
                    "confidence": float,
                    "bounding_box": [x1, y1, x2, y2], # float coordinates
                    "mask": Optional[Any] # For segmentation models
                }
            ],
            "execution_time_ms": float,
            "error_message": Optional[str]
        }
        """
        pass
