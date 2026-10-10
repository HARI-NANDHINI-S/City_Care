import os
import json
import uuid
import random
from typing import Dict, Any, List
from PIL import Image
import numpy as np

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

from app.core.config import settings
from app.models.issue import IssueType
from app.services.routing_service import get_recommended_department_name, get_recommended_department_code
from app.services.priority_service import calculate_priority_score, get_severity_from_priority

CLASSES_LIST = [
    IssueType.POTHOLE.value,
    IssueType.GARBAGE.value,
    IssueType.WATERLOGGING.value,
    IssueType.STREETLIGHT.value,
    IssueType.MANHOLE.value,
    IssueType.ROAD_DAMAGE.value,
]

def generate_dev_heuristic_analysis(image_path: str) -> Dict[str, Any]:
    # Development fallback remains ONLY for tests or explicit demo routes,
    # but MUST NOT be used in the production AI path.
    return {
        "error": "Heuristic fallback is disabled in production.",
        "is_real_yolo": False
    }

def analyze_issue_image(image_path: str) -> Dict[str, Any]:
    filename = os.path.basename(image_path)
    try:
        with Image.open(image_path) as img:
            width, height = img.size
    except Exception:
        width, height = 800, 600

    try:
        from app.ai_model.yolo.predict import predict as yolo_predict
        yolo_result = yolo_predict(image_path)
    except Exception as e:
        yolo_result = {"status": "error", "reason": f"YOLO model failed to load or predict: {str(e)}"}
    
    if yolo_result.get("status") != "success":
        return {
            "error": "Real YOLO model not available.",
            "is_real_yolo": False,
            "reason": yolo_result.get("reason", "YOLO model failed to load or predict.")
        }
        
    detections = yolo_result.get("detections", [])
    
    # 1. Verify class mapping: Map known RDD2020 classes
    YOLO_CLASS_MAPPING = {
        "D00": IssueType.ROAD_DAMAGE.value,
        "D10": IssueType.ROAD_DAMAGE.value,
        "D20": IssueType.ROAD_DAMAGE.value,
        "D40": IssueType.POTHOLE.value,
    }
    
    valid_detections = []
    for det in detections:
        raw_class = det["class"]
        # If it's already a valid IssueType, keep it. Otherwise check mapping.
        mapped_class = raw_class if raw_class in CLASSES_LIST else YOLO_CLASS_MAPPING.get(raw_class)
        if mapped_class:
            det["mapped_class"] = mapped_class
            valid_detections.append(det)
            
    if not valid_detections:
        return {
            "status": "no_detection",
            "message": "No supported civic issue detected in the image",
            "issue_type": None,
            "confidence": None,
            "severity": None,
            "priority_score": None,
            "recommended_department": None,
            "recommended_department_code": None,
            "bounding_boxes": [],
            "defect_area_ratio": 0.0,
            "annotated_image_filename": filename,
            "original_image_filename": filename,
            "is_real_yolo": True,
            "count": 0
        }

    # Pick the highest confidence detection
    best_detection = max(valid_detections, key=lambda x: x["confidence"])
    mapped_type = best_detection["mapped_class"]
    confidence = best_detection["confidence"]
    
    # Calculate defect area ratio for priority
    total_area = width * height
    box_area = 0
    bounding_boxes = []
    
    for det in valid_detections:
        coords = det["bounding_box"]
        x1, y1, x2, y2 = coords
        w = x2 - x1
        h = y2 - y1
        box_area += (w * h)
        bounding_boxes.append({
            "class": det["mapped_class"],  # Use mapped class here
            "raw_class": det["class"],
            "confidence": det["confidence"],
            "x": int(x1),
            "y": int(y1),
            "width": int(w),
            "height": int(h),
            "box_normalized": [
                round(x1 / width, 3),
                round(y1 / height, 3),
                round(w / width, 3),
                round(h / height, 3)
            ]
        })
        
    defect_area_ratio = round(box_area / total_area, 3) if total_area > 0 else 0.0
    defect_area_ratio = min(1.0, defect_area_ratio)

    # Annotated image (reuse existing OpenCV drawing if CV2 is available)
    annotated_filename = f"annotated_{uuid.uuid4().hex[:8]}_{filename}"
    annotated_path = os.path.join(settings.ANNOTATED_IMG_DIR, annotated_filename)

    if HAS_OPENCV:
        cv_img = cv2.imread(image_path)
        if cv_img is not None:
            for bbox in bounding_boxes:
                bx, by, bw, bh = bbox["x"], bbox["y"], bbox["width"], bbox["height"]
                cv2.rectangle(cv_img, (bx, by), (bx + bw, by + bh), (0, 255, 0), 3)
                label = f"{bbox['class']} ({int(bbox['confidence']*100)}%)"
                cv2.putText(cv_img, label, (bx + 5, by - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.imwrite(annotated_path, cv_img)
        else:
            annotated_filename = filename
    else:
        annotated_filename = filename

    priority_score = calculate_priority_score(
        issue_type=mapped_type,
        ai_confidence=confidence,
        defect_area_ratio=defect_area_ratio,
        duplicate_count=0,
        hours_unresolved=0.0
    )
    severity = get_severity_from_priority(priority_score)
    dept_name = get_recommended_department_name(mapped_type)
    dept_code = get_recommended_department_code(mapped_type)

    return {
        "status": "success",
        "issue_type": mapped_type,
        "confidence": confidence,
        "severity": severity.value,
        "priority_score": priority_score,
        "recommended_department": dept_name,
        "recommended_department_code": dept_code,
        "bounding_boxes": bounding_boxes,
        "defect_area_ratio": defect_area_ratio,
        "annotated_image_filename": annotated_filename,
        "original_image_filename": filename,
        "is_real_yolo": True,
        "count": len(bounding_boxes)
    }

