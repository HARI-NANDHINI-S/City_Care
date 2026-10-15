import os
import math
import json
import uuid
import time
from typing import Dict, Any, List, Optional
from PIL import Image
import numpy as np

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

from app.core.config import settings
from app.core.defect_registry import DEFECT_REGISTRY, get_category_spec
from app.services.routing_service import get_recommended_department_name, get_recommended_department_code
from app.services.priority_service import calculate_priority_score, get_severity_from_priority
from app.services.models.registry import model_registry

def _is_valid_detection_dict(det: Any) -> bool:
    """Verify that a detection output is a dictionary with a valid class name and finite numeric confidence."""
    if not isinstance(det, dict):
        return False
    cls_name = det.get("class")
    if not cls_name or not isinstance(cls_name, str):
        return False
    conf = det.get("confidence")
    if conf is None or not isinstance(conf, (int, float)):
        return False
    try:
        conf_val = float(conf)
        if not math.isfinite(conf_val):
            return False
        if not (0.0 <= conf_val <= 1.0):
            return False
    except (TypeError, ValueError):
        return False
    return True

def _is_valid_bounding_box(coords: Any, width: int, height: int) -> bool:
    """
    Verify that coords is a valid 4-element bounding box [x1, y1, x2, y2]
    with non-inverted coordinates within valid non-negative bounds.
    """
    if coords is None or not isinstance(coords, (list, tuple)) or len(coords) != 4:
        return False
    try:
        x1, y1, x2, y2 = coords
        if not all(isinstance(c, (int, float)) for c in (x1, y1, x2, y2)):
            return False
        x1, y1, x2, y2 = float(x1), float(y1), float(x2), float(y2)
        if x1 < 0 or y1 < 0:
            return False
        if x2 <= x1 or y2 <= y1:
            return False
        return True
    except (TypeError, ValueError):
        return False

def analyze_issue_image(image_path: str) -> Dict[str, Any]:
    """
    Unified AI inference pipeline:
    Image validation -> Multi-model routing -> Multi-defect detection -> Postprocessing
    -> Model result arbitration (YOLO-first spatial precedence)
    -> Category mapping -> Priority score calculation -> Annotation generation -> Provenance recording.
    """
    filename = os.path.basename(image_path)
    
    # 1. Validate image format & dimensions
    try:
        with Image.open(image_path) as img:
            width, height = img.size
    except Exception as e:
        return {
            "status": "analysis_failed",
            "message": f"Corrupt or invalid image file: {str(e)}",
            "is_real_yolo": False,
            "detected_defects": [],
            "model_provenance": {}
        }

    # 2. Query available vision model adapters
    active_adapters = model_registry.get_all_active_adapters()
    if not active_adapters:
        return {
            "status": "vision_unavailable",
            "message": "No computer vision defect models are currently loaded or available.",
            "is_real_yolo": False,
            "detected_defects": [],
            "model_provenance": {}
        }

    all_raw_detections: List[Dict[str, Any]] = []
    model_provenance: Dict[str, Any] = {}

    for adapter in active_adapters:
        # Defense-in-depth: only invoke adapters that are confirmed available
        if not getattr(adapter, "is_available", True):
            continue

        result = adapter.infer(image_path)
        raw_list = result.get("raw_detections") if isinstance(result.get("raw_detections"), list) else []
        model_provenance[adapter.model_id] = {
            "status": result.get("status"),
            "execution_time_ms": result.get("execution_time_ms"),
            "detections_count": len(raw_list),
            "supported_categories": getattr(adapter, "supported_categories", [])
        }

        if result.get("status") == "success":
            for det in raw_list:
                if _is_valid_detection_dict(det):
                    det_copy = dict(det)
                    det_copy["source_model"] = adapter.model_id
                    all_raw_detections.append(det_copy)

    # 3. Filter by evidence-based confidence threshold and category mapping
    valid_detections: List[Dict[str, Any]] = []
    for det in all_raw_detections:
        category_name = det.get("class")
        spec = get_category_spec(category_name)
        if not spec:
            continue

        # Evidence-based threshold resolution:
        # Object detection categories use YOLO_CONFIDENCE_THRESHOLD (default 0.25).
        # Image classification categories use IRDID_CLASSIFIER_THRESHOLD (default 0.30).
        model_type = spec.get("model_type")
        if model_type == "object_detection":
            threshold = getattr(settings, "YOLO_CONFIDENCE_THRESHOLD", spec.get("confidence_threshold", 0.25))
        elif model_type == "image_classification":
            threshold = getattr(settings, "IRDID_CLASSIFIER_THRESHOLD", spec.get("confidence_threshold", 0.30))
        else:
            threshold = spec.get("confidence_threshold", 0.25)

        conf = det.get("confidence")
        if conf is None or not isinstance(conf, (int, float)):
            continue
        try:
            conf_val = float(conf)
            if not math.isfinite(conf_val):
                continue
        except (TypeError, ValueError):
            continue

        if conf_val >= threshold:
            valid_detections.append(det)

    # 4. Handle "No Defect Detected"
    if not valid_detections:
        return {
            "status": "no_detection",
            "message": "No infrastructure defect detected with sufficient confidence in this image.",
            "issue_type": None,
            "confidence": None,
            "severity": None,
            "priority_score": None,
            "recommended_department": None,
            "recommended_department_code": None,
            "bounding_boxes": [],
            "detected_defects": [],
            "defect_area_ratio": 0.0,
            "annotated_image_filename": filename,
            "original_image_filename": filename,
            "is_real_yolo": True,
            "count": 0,
            "model_provenance": model_provenance
        }

    # 5. Model Result Arbitration: Partition into localized detections and image-level classification predictions
    # Rule 1: Localized YOLO detections take precedence over image-level classification predictions.
    # Rule 4: Classification predictions may be considered ONLY when no valid localized detection exists.
    # Rule 5 & 8: Classification predictions must never be represented as localized detections (bounding_box is None).
    localized_detections: List[Dict[str, Any]] = []
    classification_detections: List[Dict[str, Any]] = []

    for det in valid_detections:
        cat_name = det.get("class")
        spec = get_category_spec(cat_name)
        model_type = spec.get("model_type") if spec else None

        coords = det.get("bounding_box")
        if model_type == "image_classification":
            # Genuine image-level classification: ensure spatial attributes remain strictly None
            det_classif = dict(det)
            det_classif["bounding_box"] = None
            classification_detections.append(det_classif)
        elif _is_valid_bounding_box(coords, width, height):
            # Genuine localized detection with valid bounding box
            localized_detections.append(det)
        else:
            # Malformed, corrupt, or missing bounding box for an object detection category — safely discard
            continue

    # 6. Arbitrate primary defect selection (YOLO-first spatial precedence)
    # Rule 1 & 3: Localized detections take strict precedence regardless of classification confidence.
    # Rule 2: All valid YOLO detections and their bounding boxes/confidence scores are preserved.
    # Rule 4: Classification predictions are considered for primary defect ONLY if zero localized detections exist.
    if localized_detections:
        best_detection = max(localized_detections, key=lambda x: x["confidence"])
        primary_category = best_detection["class"]
        primary_confidence = best_detection["confidence"]
    elif classification_detections:
        best_detection = max(classification_detections, key=lambda x: x["confidence"])
        primary_category = best_detection["class"]
        primary_confidence = best_detection["confidence"]
    else:
        return {
            "status": "no_detection",
            "message": "No infrastructure defect detected with sufficient confidence in this image.",
            "issue_type": None,
            "confidence": None,
            "severity": None,
            "priority_score": None,
            "recommended_department": None,
            "recommended_department_code": None,
            "bounding_boxes": [],
            "detected_defects": [],
            "defect_area_ratio": 0.0,
            "annotated_image_filename": filename,
            "original_image_filename": filename,
            "is_real_yolo": True,
            "count": 0,
            "model_provenance": model_provenance
        }

    # 7. Build geometry, defect area, and multi-defect details
    total_area = width * height
    box_area = 0
    bounding_boxes: List[Dict[str, Any]] = []
    detected_defects: List[Dict[str, Any]] = []

    # First, process all valid localized detections (preserving bounding boxes and geometry)
    for det in localized_detections:
        x1, y1, x2, y2 = det["bounding_box"]
        w = max(0, x2 - x1)
        h = max(0, y2 - y1)
        box_area += (w * h)

        bbox_data = {
            "class": det["class"],
            "raw_class": det.get("raw_class", det["class"]),
            "confidence": round(det["confidence"], 4),
            "x": int(x1),
            "y": int(y1),
            "width": int(w),
            "height": int(h),
            "box_normalized": [
                round(x1 / width, 3) if width > 0 else 0,
                round(y1 / height, 3) if height > 0 else 0,
                round(w / width, 3) if width > 0 else 0,
                round(h / height, 3) if height > 0 else 0
            ],
            "model_id": det.get("source_model")
        }
        bounding_boxes.append(bbox_data)
        detected_defects.append({
            "category": det["class"],
            "confidence": round(det["confidence"], 4),
            "model_id": det.get("source_model"),
            "bounding_box": [int(x1), int(y1), int(w), int(h)]
        })

    # Next, record classification detections as secondary scene-level context (bounding_box: None)
    for det in classification_detections:
        detected_defects.append({
            "category": det["class"],
            "confidence": round(det["confidence"], 4),
            "model_id": det.get("source_model"),
            "bounding_box": None
        })

    defect_area_ratio = round(box_area / total_area, 3) if total_area > 0 else 0.0
    defect_area_ratio = min(1.0, defect_area_ratio)

    # 8. Render bounding box overlay on annotated image
    annotated_filename = f"annotated_{uuid.uuid4().hex[:8]}_{filename}"
    annotated_path = os.path.join(settings.ANNOTATED_IMG_DIR, annotated_filename)

    if HAS_OPENCV:
        cv_img = cv2.imread(image_path)
        if cv_img is not None:
            # Color palette per category
            colors = {
                "Pothole": (0, 0, 255),               # Red
                "Longitudinal Crack": (255, 165, 0),   # Orange
                "Transverse Crack": (255, 255, 0),     # Yellow
                "Alligator Crack": (0, 255, 255),      # Cyan
                "Garbage Accumulation": (0, 255, 0),   # Green
                "Waterlogging": (255, 0, 255),         # Magenta
            }
            for bbox in bounding_boxes:
                bx, by, bw, bh = bbox["x"], bbox["y"], bbox["width"], bbox["height"]
                col = colors.get(bbox["class"], (0, 255, 0))
                cv2.rectangle(cv_img, (bx, by), (bx + bw, by + bh), col, 3)
                label = f"{bbox['class']} ({int(bbox['confidence']*100)}%)"
                cv2.putText(cv_img, label, (bx + 5, max(15, by - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.imwrite(annotated_path, cv_img)
        else:
            annotated_filename = filename
    else:
        annotated_filename = filename

    # 9. Calculate Priority & Severity & Routing
    priority_score = calculate_priority_score(
        issue_type=primary_category,
        ai_confidence=primary_confidence,
        defect_area_ratio=defect_area_ratio,
        duplicate_count=0,
        hours_unresolved=0.0
    )
    severity = get_severity_from_priority(priority_score)
    dept_name = get_recommended_department_name(primary_category)
    dept_code = get_recommended_department_code(primary_category)

    return {
        "status": "success",
        "issue_type": primary_category,
        "confidence": primary_confidence,
        "severity": severity.value,
        "priority_score": priority_score,
        "recommended_department": dept_name,
        "recommended_department_code": dept_code,
        "bounding_boxes": bounding_boxes,
        "detected_defects": detected_defects,
        "defect_area_ratio": defect_area_ratio,
        "annotated_image_filename": annotated_filename,
        "original_image_filename": filename,
        "is_real_yolo": (best_detection.get("source_model") == "yolov8-rdd2020-india-v1"),
        "count": len(bounding_boxes),
        "model_provenance": model_provenance
    }
