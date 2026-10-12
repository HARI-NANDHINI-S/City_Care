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
    DETECTION_SUPPORTED = "DETECTION_SUPPORTED"             # Has verified bounding-box detection weights
    CLASSIFICATION_ONLY_DATA = "CLASSIFICATION_ONLY_DATA"   # Has clean Indian image-level data; no bounding boxes
    PENDING_DATA_ACCESS = "PENDING_DATA_ACCESS"             # External Indian dataset identified but download restricted
    INSUFFICIENT_INDIAN_DATA = "INSUFFICIENT_INDIAN_DATA"   # No viable Indian dataset found yet
    FUTURE_SCOPE = "FUTURE_SCOPE"                           # Out-of-scope future module

# Comprehensive specification of all 12 target defect categories + extensions
DEFECT_REGISTRY: Dict[str, Dict[str, Any]] = {
    # -------------------------------------------------------------
    # A. ROAD-RELATED DEFECTS (5)
    # -------------------------------------------------------------
    "Pothole": {
        "domain": DefectDomain.ROAD,
        "raw_classes": ["D40"],
        "model_id": "yolov8-rdd2020-india-v1",
        "model_type": "object_detection",
        "readiness": ModelReadinessStatus.DETECTION_SUPPORTED,
        "default_dept_code": "DEPT_PWD",
        "default_dept_name": "Road & Public Works Department",
        "base_risk_score": 75.0,
        "confidence_threshold": 0.25,
        "description": "Cavity or depression formed in asphalt/concrete surface."
    },
    "Longitudinal Crack": {
        "domain": DefectDomain.ROAD,
        "raw_classes": ["D00"],
        "model_id": "yolov8-rdd2020-india-v1",
        "model_type": "object_detection",
        "readiness": ModelReadinessStatus.DETECTION_SUPPORTED,
        "default_dept_code": "DEPT_PWD",
        "default_dept_name": "Road & Public Works Department",
        "base_risk_score": 60.0,
        "confidence_threshold": 0.25,
        "description": "Fracture extending along the road direction parallel to traffic."
    },
    "Transverse Crack": {
        "domain": DefectDomain.ROAD,
        "raw_classes": ["D10"],
        "model_id": "yolov8-rdd2020-india-v1",
        "model_type": "object_detection",
        "readiness": ModelReadinessStatus.DETECTION_SUPPORTED,
        "default_dept_code": "DEPT_PWD",
        "default_dept_name": "Road & Public Works Department",
        "base_risk_score": 60.0,
        "confidence_threshold": 0.25,
        "description": "Fracture extending perpendicular to the road centerline."
    },
    "Alligator Crack": {
        "domain": DefectDomain.ROAD,
        "raw_classes": ["D20"],
        "model_id": "yolov8-rdd2020-india-v1",
        "model_type": "object_detection",
        "readiness": ModelReadinessStatus.DETECTION_SUPPORTED,
        "default_dept_code": "DEPT_PWD",
        "default_dept_name": "Road & Public Works Department",
        "base_risk_score": 70.0,
        "confidence_threshold": 0.25,
        "description": "Interconnected fatigue fractures resembling reptilian skin."
    },
    "Damaged Road Surface": {
        "domain": DefectDomain.ROAD,
        "raw_classes": ["broken_edges"],
        "model_id": "irdid-classifier-candidate",
        "model_type": "image_classification",
        "readiness": ModelReadinessStatus.CLASSIFICATION_ONLY_DATA,
        "default_dept_code": "DEPT_PWD",
        "default_dept_name": "Road & Public Works Department",
        "base_risk_score": 65.0,
        "confidence_threshold": 0.30,
        "description": "Severe raveling, broken road shoulder, or weathered pavement (IRDID broken_edges: 67 unique images)."
    },
    # Umbrella backward compatibility
    "Road Damage": {
        "domain": DefectDomain.ROAD,
        "raw_classes": ["D00", "D10", "D20"],
        "model_id": "yolov8-rdd2020-india-v1",
        "model_type": "object_detection",
        "readiness": ModelReadinessStatus.DETECTION_SUPPORTED,
        "default_dept_code": "DEPT_PWD",
        "default_dept_name": "Road & Public Works Department",
        "base_risk_score": 65.0,
        "confidence_threshold": 0.25,
        "description": "General road surface crack or structural defect."
    },

    # -------------------------------------------------------------
    # B. SANITATION DEFECTS (3)
    # -------------------------------------------------------------
    "Garbage Accumulation": {
        "domain": DefectDomain.SANITATION,
        "raw_classes": ["garbage"],
        "model_id": None,
        "model_type": "object_detection",
        "readiness": ModelReadinessStatus.PENDING_DATA_ACCESS,
        "default_dept_code": "DEPT_SAN",
        "default_dept_name": "Waste Management & Sanitation Dept",
        "base_risk_score": 50.0,
        "confidence_threshold": 0.30,
        "description": "Accumulated solid waste. (DataCluster Labs dataset pending licensing request)."
    },
    "Illegal Dumping": {
        "domain": DefectDomain.SANITATION,
        "raw_classes": ["illegal_dump"],
        "model_id": None,
        "model_type": "object_detection",
        "readiness": ModelReadinessStatus.PENDING_DATA_ACCESS,
        "default_dept_code": "DEPT_SAN",
        "default_dept_name": "Waste Management & Sanitation Dept",
        "base_risk_score": 55.0,
        "confidence_threshold": 0.30,
        "description": "Unauthorized large-scale disposal of rubble or commercial waste."
    },
    "Overflowing Garbage Bins": {
        "domain": DefectDomain.SANITATION,
        "raw_classes": ["overflowing_bin"],
        "model_id": None,
        "model_type": "object_detection",
        "readiness": ModelReadinessStatus.PENDING_DATA_ACCESS,
        "default_dept_code": "DEPT_SAN",
        "default_dept_name": "Waste Management & Sanitation Dept",
        "base_risk_score": 52.0,
        "confidence_threshold": 0.30,
        "description": "Municipal dustbin exceeding capacity with waste spilling onto street."
    },

    # -------------------------------------------------------------
    # C. DRAINAGE DEFECTS (4)
    # -------------------------------------------------------------
    "Blocked Drains": {
        "domain": DefectDomain.DRAINAGE,
        "raw_classes": ["blocked_drain"],
        "model_id": None,
        "model_type": "object_detection",
        "readiness": ModelReadinessStatus.INSUFFICIENT_INDIAN_DATA,
        "default_dept_code": "DEPT_DRAIN",
        "default_dept_name": "Stormwater Drainage Dept",
        "base_risk_score": 75.0,
        "confidence_threshold": 0.30,
        "description": "Stormwater canal or culvert clogged by silt or debris. Requires field collection."
    },
    "Overflowing Drains": {
        "domain": DefectDomain.DRAINAGE,
        "raw_classes": ["overflowing_drain"],
        "model_id": None,
        "model_type": "object_detection",
        "readiness": ModelReadinessStatus.INSUFFICIENT_INDIAN_DATA,
        "default_dept_code": "DEPT_DRAIN",
        "default_dept_name": "Stormwater Drainage Dept",
        "base_risk_score": 80.0,
        "confidence_threshold": 0.30,
        "description": "Drain water spilling over canal banks onto roadways. Requires field collection."
    },
    "Waterlogging": {
        "domain": DefectDomain.DRAINAGE,
        "raw_classes": ["waterlogged_roads"],
        "model_id": "irdid-classifier-candidate",
        "model_type": "image_classification",
        "readiness": ModelReadinessStatus.CLASSIFICATION_ONLY_DATA,
        "default_dept_code": "DEPT_DRAIN",
        "default_dept_name": "Stormwater Drainage Dept",
        "base_risk_score": 80.0,
        "confidence_threshold": 0.30,
        "description": "Road section submerged in standing flood water (IRDID waterlogged_roads: 95 unique images)."
    },
    "Damaged Drainage Covers": {
        "domain": DefectDomain.DRAINAGE,
        "raw_classes": ["damaged_drain_grate"],
        "model_id": None,
        "model_type": "object_detection",
        "readiness": ModelReadinessStatus.INSUFFICIENT_INDIAN_DATA,
        "default_dept_code": "DEPT_DRAIN",
        "default_dept_name": "Stormwater Drainage Dept",
        "base_risk_score": 90.0,
        "confidence_threshold": 0.30,
        "description": "Broken, collapsed, or displaced stormwater drain slabs/culvert grates. Distinct from sewer manholes."
    },

    # -------------------------------------------------------------
    # D. UTILITY CIVIC DEFECTS (Distinct from drainage covers)
    # -------------------------------------------------------------
    "Open Manhole": {
        "domain": DefectDomain.UTILITY,
        "raw_classes": ["open_manholes"],
        "model_id": "irdid-classifier-candidate",
        "model_type": "image_classification",
        "readiness": ModelReadinessStatus.CLASSIFICATION_ONLY_DATA,
        "default_dept_code": "DEPT_SEW",
        "default_dept_name": "Sewerage & Sanitation Board",
        "base_risk_score": 95.0,
        "confidence_threshold": 0.30,
        "description": "Exposed underground sewer shaft opening (IRDID open_manholes: 59 unique images)."
    },
    "Broken Streetlight": {
        "domain": DefectDomain.UTILITY,
        "raw_classes": ["broken_streetlight"],
        "model_id": None,
        "model_type": "object_detection",
        "readiness": ModelReadinessStatus.INSUFFICIENT_INDIAN_DATA,
        "default_dept_code": "DEPT_ELEC",
        "default_dept_name": "Electrical Infrastructure Dept",
        "base_risk_score": 50.0,
        "confidence_threshold": 0.30,
        "description": "Non-functioning, damaged, or unshielded street luminaire."
    }
}

# Future Scope Modules Extension Point
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

def get_all_categories() -> List[str]:
    return list(DEFECT_REGISTRY.keys())
