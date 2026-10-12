from typing import Dict, Any, List, Optional
from app.services.models.base_adapter import BaseDefectModelAdapter
from app.services.models.yolo_adapter import YOLOv8RoadDamageAdapter
from app.services.models.pending_adapter import PendingModelAdapter

class ModelRegistry:
    """
    Central registry managing vision model adapters.
    Supports lazy loading and independent routing per category.
    """

    def __init__(self):
        self._adapters: Dict[str, BaseDefectModelAdapter] = {}
        self._initialize_adapters()

    def _initialize_adapters(self):
        # 1. Active YOLOv8 Road Damage model
        yolo_adapter = YOLOv8RoadDamageAdapter()
        self._adapters[yolo_adapter.model_id] = yolo_adapter

        # 2. Sanitation Model Adapter (Pending training on Indian Domestic Trash / Waste dataset)
        sanitation_adapter = PendingModelAdapter(
            model_id="sanitation-detector-v1",
            supported_categories=["Garbage Accumulation", "Illegal Dumping", "Overflowing Garbage Bins"],
            blocker_reason="Sanitation defect detector is pending manual training on Indian waste dataset."
        )
        self._adapters[sanitation_adapter.model_id] = sanitation_adapter

        # 3. Drainage Model Adapter (Pending training on Indian drainage / flood dataset)
        drainage_adapter = PendingModelAdapter(
            model_id="drainage-detector-v1",
            supported_categories=["Blocked Drains", "Overflowing Drains", "Waterlogging", "Damaged Drainage Covers"],
            blocker_reason="Drainage defect detector is pending manual training on Indian open drainage dataset."
        )
        self._adapters[drainage_adapter.model_id] = drainage_adapter

        # 4. Utility Model Adapter
        utility_adapter = PendingModelAdapter(
            model_id="utility-safety-v1",
            supported_categories=["Open Manhole", "Broken Streetlight"],
            blocker_reason="Utility safety model is pending dedicated training."
        )
        self._adapters[utility_adapter.model_id] = utility_adapter

    def get_adapter_for_category(self, category: str) -> Optional[BaseDefectModelAdapter]:
        for adapter in self._adapters.values():
            if category in adapter.supported_categories:
                return adapter
        return None

    def get_all_active_adapters(self) -> List[BaseDefectModelAdapter]:
        return [adapter for adapter in self._adapters.values() if adapter.is_available]

    def get_adapter(self, model_id: str) -> Optional[BaseDefectModelAdapter]:
        return self._adapters.get(model_id)

    def get_registry_status(self) -> Dict[str, Any]:
        return {
            model_id: {
                "available": adapter.is_available,
                "supported_categories": adapter.supported_categories
            }
            for model_id, adapter in self._adapters.items()
        }

# Global Singleton
model_registry = ModelRegistry()
