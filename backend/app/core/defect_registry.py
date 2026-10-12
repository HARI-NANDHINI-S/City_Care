from typing import Dict, Any, List, Optional
from enum import Enum

class DefectDomain(str, Enum):
    ROAD = "ROAD"
    SANITATION = "SANITATION"
    DRAINAGE = "DRAINAGE"
    UTILITY = "UTILITY"
    # Future extension points (kept clean and distinct):
    PUBLIC_INFRASTRUCTURE = "PUBLIC_INFRASTRUCTURE"
    PEDESTRIAN_INFRASTRUCTURE = "PEDESTRIAN_INFRASTRUCTURE"

class ModelReadinessStatus(str, Enum):
    # The primary capability & runtime readiness states:
    OBJECT_DETECTION_SUPPORTED = "OBJECT_DETECTION_SUPPORTED" # Object detection supported by a compatible model
    CLASSIFICATION_AVAILABLE = "CLASSIFICATION_AVAILABLE"     # Classification model available (weights loaded)
    CLASSIFICATION_UNAVAILABLE = "CLASSIFICATION_UNAVAILABLE" # Classification intended but model unavailable (weights not loaded)
    IMAGE_CLASSIFICATION_ONLY = "IMAGE_CLASSIFICATION_ONLY"   # Intended whole-image / scene classification (no bounding boxes)
    PENDING_MANUAL_TRAINING = "PENDING_MANUAL_TRAINING"       # Manual reporting only — pending model training
    INSUFFICIENT_SUITABLE_DATA = "INSUFFICIENT_SUITABLE_DATA" # Manual reporting only — insufficient suitable data
    MANUAL_REPORTING_ONLY = "MANUAL_REPORTING_ONLY"           # Manual reporting only
    ANALYSIS_FAILED = "ANALYSIS_FAILED"                       # Analysis failed (corrupted or unreadable image)

    # Future scope extension state:
    FUTURE_SCOPE = "FUTURE_SCOPE"                             # Out-of-scope future module (unimplemented)

    # Aliases for backward compatibility:
    DETECTION_SUPPORTED = "OBJECT_DETECTION_SUPPORTED"
    CLASSIFICATION_ONLY_DATA = "IMAGE_CLASSIFICATION_ONLY"
    PENDING_DATA_ACCESS = "PENDING_MANUAL_TRAINING"
    INSUFFICIENT_INDIAN_DATA = "INSUFFICIENT_SUITABLE_DATA"

READINESS_LABELS: Dict[str, str] = {
    ModelReadinessStatus.OBJECT_DETECTION_SUPPORTED.value: "Object detection supported by a compatible model",
    ModelReadinessStatus.CLASSIFICATION_AVAILABLE.value: "Classification model available",
    ModelReadinessStatus.CLASSIFICATION_UNAVAILABLE.value: "Classification intended (model unavailable)",
    ModelReadinessStatus.IMAGE_CLASSIFICATION_ONLY.value: "Classification intended (model unavailable)",
    ModelReadinessStatus.PENDING_MANUAL_TRAINING.value: "Manual reporting only (pending training)",
    ModelReadinessStatus.INSUFFICIENT_SUITABLE_DATA.value: "Manual reporting only (insufficient suitable data)",
    ModelReadinessStatus.MANUAL_REPORTING_ONLY.value: "Manual reporting only",
    ModelReadinessStatus.ANALYSIS_FAILED.value: "Analysis failed",
    ModelReadinessStatus.FUTURE_SCOPE.value: "Future extension (unimplemented)"
}

# The Active 12-Category Scope (Roads: 5, Sanitation: 3, Drainage: 4)
ACTIVE_12_CATEGORIES: List[str] = [
    # Roads (5)
    "Pothole",
    "Longitudinal Crack",
    "Transverse Crack",
    "Alligator Crack",
    "Damaged Road Surface",
    # Sanitation (3)
    "Garbage Accumulation",
    "Illegal Dumping",
    "Overflowing Garbage Bins",
    # Drainage (4)
    "Blocked Drains",
    "Overflowing Drains",
    "Waterlogging",
    "Damaged Drainage Covers"
]

# Comprehensive specification of all 12 target defect categories + legacy/utility records
DEFECT_REGISTRY: Dict[str, Dict[str, Any]] = {
    # -------------------------------------------------------------
    # A. ROAD-RELATED DEFECTS (5 Active)
    # -------------------------------------------------------------
    "Pothole": {
        "domain": DefectDomain.ROAD,
        "is_active_scope": True,
        "raw_classes": ["D40"],
        "model_id": "yolov8-rdd2020-india-v1",
        "model_type": "object_detection",
        "readiness": ModelReadinessStatus.OBJECT_DETECTION_SUPPORTED,
        "default_dept_code": "DEPT_PWD",
        "default_dept_name": "Road & Public Works Department",
        "base_risk_score": 75.0,
        "confidence_threshold": 0.25,
        "description": "Cavity or depression formed in asphalt/concrete surface."
    },
    "Longitudinal Crack": {
        "domain": DefectDomain.ROAD,
        "is_active_scope": True,
        "raw_classes": ["D00"],
        "model_id": "yolov8-rdd2020-india-v1",
        "model_type": "object_detection",
        "readiness": ModelReadinessStatus.OBJECT_DETECTION_SUPPORTED,
        "default_dept_code": "DEPT_PWD",
        "default_dept_name": "Road & Public Works Department",
        "base_risk_score": 60.0,
        "confidence_threshold": 0.25,
        "description": "Fracture extending along the road direction parallel to traffic."
    },
    "Transverse Crack": {
        "domain": DefectDomain.ROAD,
        "is_active_scope": True,
        "raw_classes": ["D10"],
        "model_id": "yolov8-rdd2020-india-v1",
        "model_type": "object_detection",
        "readiness": ModelReadinessStatus.OBJECT_DETECTION_SUPPORTED,
        "default_dept_code": "DEPT_PWD",
        "default_dept_name": "Road & Public Works Department",
        "base_risk_score": 60.0,
        "confidence_threshold": 0.25,
        "description": "Fracture extending perpendicular to the road centerline (9 test instances in RDD2020 India)."
    },
    "Alligator Crack": {
        "domain": DefectDomain.ROAD,
        "is_active_scope": True,
        "raw_classes": ["D20"],
        "model_id": "yolov8-rdd2020-india-v1",
        "model_type": "object_detection",
        "readiness": ModelReadinessStatus.OBJECT_DETECTION_SUPPORTED,
        "default_dept_code": "DEPT_PWD",
        "default_dept_name": "Road & Public Works Department",
        "base_risk_score": 70.0,
        "confidence_threshold": 0.25,
        "description": "Interconnected fatigue fractures resembling reptilian skin."
    },
    "Damaged Road Surface": {
        "domain": DefectDomain.ROAD,
        "is_active_scope": True,
        "raw_classes": ["broken_edges"],
        "model_id": "irdid-classifier-candidate",
        "model_type": "image_classification",
        "readiness": ModelReadinessStatus.IMAGE_CLASSIFICATION_ONLY,
        "default_dept_code": "DEPT_PWD",
        "default_dept_name": "Road & Public Works Department",
        "base_risk_score": 65.0,
        "confidence_threshold": 0.30,
        "description": "Severe raveling, broken road shoulder, or weathered pavement (IRDID broken_edges: 67 unique images; image classification only, no bounding boxes)."
    },

    # -------------------------------------------------------------
    # B. SANITATION DEFECTS (3 Active)
    # -------------------------------------------------------------
    "Garbage Accumulation": {
        "domain": DefectDomain.SANITATION,
        "is_active_scope": True,
        "raw_classes": ["garbage"],
        "model_id": None,
        "model_type": "object_detection",
        "readiness": ModelReadinessStatus.PENDING_MANUAL_TRAINING,
        "default_dept_code": "DEPT_SAN",
        "default_dept_name": "Waste Management & Sanitation Dept",
        "base_risk_score": 50.0,
        "confidence_threshold": 0.30,
        "description": "Accumulated solid waste (DataCluster Labs Indian Domestic Trash dataset pending licensing/training)."
    },
    "Illegal Dumping": {
        "domain": DefectDomain.SANITATION,
        "is_active_scope": True,
        "raw_classes": ["illegal_dump"],
        "model_id": None,
        "model_type": "object_detection",
        "readiness": ModelReadinessStatus.PENDING_MANUAL_TRAINING,
        "default_dept_code": "DEPT_SAN",
        "default_dept_name": "Waste Management & Sanitation Dept",
        "base_risk_score": 55.0,
        "confidence_threshold": 0.30,
        "description": "Unauthorized large-scale disposal of rubble or commercial waste."
    },
    "Overflowing Garbage Bins": {
        "domain": DefectDomain.SANITATION,
        "is_active_scope": True,
        "raw_classes": ["overflowing_bin"],
        "model_id": None,
        "model_type": "object_detection",
        "readiness": ModelReadinessStatus.PENDING_MANUAL_TRAINING,
        "default_dept_code": "DEPT_SAN",
        "default_dept_name": "Waste Management & Sanitation Dept",
        "base_risk_score": 52.0,
        "confidence_threshold": 0.30,
        "description": "Municipal dustbin exceeding capacity with waste spilling onto street."
    },

    # -------------------------------------------------------------
    # C. DRAINAGE DEFECTS (4 Active)
    # -------------------------------------------------------------
    "Blocked Drains": {
        "domain": DefectDomain.DRAINAGE,
        "is_active_scope": True,
        "raw_classes": ["blocked_drain"],
        "model_id": None,
        "model_type": "object_detection",
        "readiness": ModelReadinessStatus.INSUFFICIENT_SUITABLE_DATA,
        "default_dept_code": "DEPT_DRAIN",
        "default_dept_name": "Stormwater Drainage Dept",
        "base_risk_score": 75.0,
        "confidence_threshold": 0.30,
        "description": "Stormwater canal or culvert clogged by silt or debris. Requires Indian field collection."
    },
    "Overflowing Drains": {
        "domain": DefectDomain.DRAINAGE,
        "is_active_scope": True,
        "raw_classes": ["overflowing_drain"],
        "model_id": None,
        "model_type": "object_detection",
        "readiness": ModelReadinessStatus.INSUFFICIENT_SUITABLE_DATA,
        "default_dept_code": "DEPT_DRAIN",
        "default_dept_name": "Stormwater Drainage Dept",
        "base_risk_score": 80.0,
        "confidence_threshold": 0.30,
        "description": "Drain water spilling over canal banks onto roadways. Requires Indian field collection."
    },
    "Waterlogging": {
        "domain": DefectDomain.DRAINAGE,
        "is_active_scope": True,
        "raw_classes": ["waterlogged_roads"],
        "model_id": "irdid-classifier-candidate",
        "model_type": "image_classification",
        "readiness": ModelReadinessStatus.IMAGE_CLASSIFICATION_ONLY,
        "default_dept_code": "DEPT_DRAIN",
        "default_dept_name": "Stormwater Drainage Dept",
        "base_risk_score": 80.0,
        "confidence_threshold": 0.30,
        "description": "Whole-image road scene submerged in flood water (IRDID waterlogged_roads: 95 unique images; distinct from localized water-region detection; image classification only, no bounding boxes)."
    },
    "Damaged Drainage Covers": {
        "domain": DefectDomain.DRAINAGE,
        "is_active_scope": True,
        "raw_classes": ["damaged_drain_grate"],
        "model_id": None,
        "model_type": "object_detection",
        "readiness": ModelReadinessStatus.INSUFFICIENT_SUITABLE_DATA,
        "default_dept_code": "DEPT_DRAIN",
        "default_dept_name": "Stormwater Drainage Dept",
        "base_risk_score": 90.0,
        "confidence_threshold": 0.30,
        "description": "Broken, collapsed, or displaced stormwater drain slabs/culvert grates. Strictly distinct from open sewer manholes."
    },

    # -------------------------------------------------------------
    # D. OUTSIDE ACTIVE 12-CATEGORY SCOPE (Preserved for backward compatibility & DB records)
    # -------------------------------------------------------------
    "Road Damage": {
        "domain": DefectDomain.ROAD,
        "is_active_scope": False,
        "raw_classes": ["D00", "D10", "D20"],
        "model_id": "yolov8-rdd2020-india-v1",
        "model_type": "object_detection",
        "readiness": ModelReadinessStatus.OBJECT_DETECTION_SUPPORTED,
        "default_dept_code": "DEPT_PWD",
        "default_dept_name": "Road & Public Works Department",
        "base_risk_score": 65.0,
        "confidence_threshold": 0.25,
        "description": "Legacy umbrella road defect. Excluded from active 12-category workflow."
    },
    "Open Manhole": {
        "domain": DefectDomain.UTILITY,
        "is_active_scope": False,
        "raw_classes": ["open_manholes"],
        "model_id": "irdid-classifier-candidate",
        "model_type": "image_classification",
        "readiness": ModelReadinessStatus.IMAGE_CLASSIFICATION_ONLY,
        "default_dept_code": "DEPT_SEW",
        "default_dept_name": "Sewerage & Sanitation Board",
        "base_risk_score": 95.0,
        "confidence_threshold": 0.30,
        "description": "Exposed underground sewer shaft opening (IRDID open_manholes: 59 unique images). Kept outside active 12-category scope and distinct from damaged drainage covers."
    },
    "Broken Streetlight": {
        "domain": DefectDomain.UTILITY,
        "is_active_scope": False,
        "raw_classes": ["broken_streetlight"],
        "model_id": None,
        "model_type": "object_detection",
        "readiness": ModelReadinessStatus.INSUFFICIENT_SUITABLE_DATA,
        "default_dept_code": "DEPT_ELEC",
        "default_dept_name": "Electrical Infrastructure Dept",
        "base_risk_score": 50.0,
        "confidence_threshold": 0.30,
        "description": "Non-functioning, damaged, or unshielded street luminaire. Kept outside active 12-category scope."
    }
}

# Future Scope Modules Extension Point (Kept strictly unimplemented)
FUTURE_EXTENSION_REGISTRY = {
    DefectDomain.PUBLIC_INFRASTRUCTURE: {
        "title": "Public Infrastructure Defects",
        "scope": "Future Scope — Not Implemented in Active Pipeline",
        "intended_categories": ["Damaged Bridges", "Collapsed Retaining Walls", "Damaged Bus Shelters"],
        "status": ModelReadinessStatus.FUTURE_SCOPE
    },
    DefectDomain.PEDESTRIAN_INFRASTRUCTURE: {
        "title": "Pedestrian Infrastructure Defects",
        "scope": "Future Scope — Not Implemented in Active Pipeline",
        "intended_categories": ["Broken Footpaths", "Missing Tactile Paving", "Damaged Pedestrian Guardrails"],
        "status": ModelReadinessStatus.FUTURE_SCOPE
    }
}

def get_category_spec(category_name: str) -> Optional[Dict[str, Any]]:
    return DEFECT_REGISTRY.get(category_name)

def get_active_categories() -> List[Dict[str, Any]]:
    """Returns the metadata and runtime capability status for the active 12 categories."""
    from app.services.models.registry import model_registry
    result = []
    for name in ACTIVE_12_CATEGORIES:
        spec = DEFECT_REGISTRY.get(name, {})
        model_id = spec.get("model_id")
        adapter = model_registry.get_adapter(model_id) if model_id else None
        is_model_available = adapter.is_available if adapter else False

        readiness_val = spec.get("readiness")
        readiness_str = readiness_val.value if isinstance(readiness_val, ModelReadinessStatus) else str(readiness_val)

        # Distinguish exact runtime capability
        if spec.get("model_type") == "object_detection":
            if is_model_available:
                capability_category = "OBJECT_DETECTION_SUPPORTED"
                runtime_readiness = ModelReadinessStatus.OBJECT_DETECTION_SUPPORTED.value
                runtime_label = "Object detection supported by a compatible model"
            else:
                capability_category = "MANUAL_REPORTING_ONLY"
                runtime_readiness = readiness_str
                runtime_label = READINESS_LABELS.get(runtime_readiness, "Manual reporting only")
        elif spec.get("model_type") == "image_classification":
            if is_model_available:
                capability_category = "CLASSIFICATION_AVAILABLE"
                runtime_readiness = ModelReadinessStatus.CLASSIFICATION_AVAILABLE.value
                runtime_label = "Classification model available"
            else:
                capability_category = "CLASSIFICATION_UNAVAILABLE"
                runtime_readiness = ModelReadinessStatus.CLASSIFICATION_UNAVAILABLE.value
                runtime_label = "Classification intended (model unavailable)"
        else:
            capability_category = "MANUAL_REPORTING_ONLY"
            runtime_readiness = ModelReadinessStatus.MANUAL_REPORTING_ONLY.value
            runtime_label = "Manual reporting only"

        result.append({
            "name": name,
            "domain": spec.get("domain", "").value if hasattr(spec.get("domain"), "value") else str(spec.get("domain")),
            "is_active_scope": True,
            "readiness": readiness_str,
            "readiness_label": READINESS_LABELS.get(readiness_str, readiness_str),
            "runtime_readiness": runtime_readiness,
            "runtime_label": runtime_label,
            "capability_category": capability_category,
            "model_type": spec.get("model_type"),
            "model_id": model_id,
            "model_loaded": is_model_available,
            "default_dept_code": spec.get("default_dept_code"),
            "default_dept_name": spec.get("default_dept_name"),
            "base_risk_score": spec.get("base_risk_score"),
            "description": spec.get("description")
        })
    return result

def get_all_categories() -> List[str]:
    return list(DEFECT_REGISTRY.keys())
