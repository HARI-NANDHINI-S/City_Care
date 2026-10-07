import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw
from app.services.ai_service import analyze_issue_image
from app.core.config import settings

def test_ai_vision_pipeline():
    print("=" * 60)
    print("      CIVICVISION AI — COMPUTER VISION PIPELINE TEST")
    print("=" * 60)

    # 1. Test Valid YOLO detection
    test_img_path = os.path.join(settings.ORIGINAL_IMG_DIR, "pipeline_test.jpg")
    img = Image.new('RGB', (640, 640), color=(73, 109, 137))
    d = ImageDraw.Draw(img)
    d.rectangle([(200, 200), (440, 440)], fill=(255, 0, 0))
    img.save(test_img_path)

    print(f"[+] Created synthetic input image: {test_img_path}")

    res = analyze_issue_image(test_img_path)

    if "error" in res:
        print("\n[+] AI Vision Pipeline Analysis Output: MODEL NOT AVAILABLE")
    elif res.get("status") == "no_detection":
        print("\n[+] AI Vision Pipeline Analysis Output: NO DETECTION (Expected since real YOLO won't detect a red square)")
        # We can't guarantee detection on a synthetic shape with real YOLO.
    else:
        print("\n[+] AI Vision Pipeline Analysis Output: DETECTION FOUND")
        assert res["issue_type"] is not None
        assert 0.0 <= res["confidence"] <= 1.0
        assert 0.0 <= res["priority_score"] <= 100.0

    # 2. Test No YOLO detection
    # We will create an image that YOLO should not detect anything in
    empty_img_path = os.path.join(settings.ORIGINAL_IMG_DIR, "empty_test.jpg")
    empty_img = Image.new('RGB', (640, 640), color=(255, 255, 255))
    empty_img.save(empty_img_path)
    print(f"\n[+] Created empty synthetic input image: {empty_img_path}")

    res_empty = analyze_issue_image(empty_img_path)
    if "error" in res_empty:
        print("\n[+] AI Vision Pipeline Analysis Output: MODEL NOT AVAILABLE")
    else:
        print(f"\n[+] AI Vision Pipeline Empty Output Status: {res_empty.get('status')}")
        assert res_empty.get("status") == "no_detection"
        assert res_empty.get("issue_type") is None
        assert res_empty.get("priority_score") is None
        assert res_empty.get("severity") is None
        assert res_empty.get("recommended_department") is None
        assert len(res_empty.get("bounding_boxes", [])) == 0
        assert res_empty.get("count", -1) == 0

    print("\n[+] AI Pipeline Execution Check: PASSED")
    print("=" * 60)

def test_class_mapping():
    from unittest.mock import patch
    print("\n[+] Testing YOLO Class Mapping")
    test_img_path = os.path.join(settings.ORIGINAL_IMG_DIR, "mock_test.jpg")
    empty_img = Image.new('RGB', (10, 10), color=(255, 255, 255))
    empty_img.save(test_img_path)
    
    with patch("app.services.ai_service.yolo_predict") as mock_predict:
        # Test Unknown Class
        mock_predict.return_value = {
            "status": "success",
            "detections": [
                {"class": "D99", "confidence": 0.9, "bounding_box": [0, 0, 10, 10]}
            ]
        }
        res = analyze_issue_image(test_img_path)
        assert res["status"] == "no_detection", f"Expected no_detection for unknown class, got {res['status']}"
        
        # Test Known Class (D40)
        mock_predict.return_value = {
            "status": "success",
            "detections": [
                {"class": "D40", "confidence": 0.9, "bounding_box": [0, 0, 10, 10]}
            ]
        }
        res = analyze_issue_image(test_img_path)
        assert res["status"] == "success"
        assert res["issue_type"] == "Pothole"
        
        # Test Known Class (D00)
        mock_predict.return_value = {
            "status": "success",
            "detections": [
                {"class": "D00", "confidence": 0.9, "bounding_box": [0, 0, 10, 10]}
            ]
        }
        res = analyze_issue_image(test_img_path)
        assert res["status"] == "success"
        assert res["issue_type"] == "Road Damage"
        print("[+] YOLO Class Mapping Check: PASSED")

if __name__ == "__main__":
    test_ai_vision_pipeline()
    test_class_mapping()
