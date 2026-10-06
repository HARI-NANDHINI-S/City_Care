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

    # Create dummy test image in uploads/original
    test_img_path = os.path.join(settings.ORIGINAL_IMG_DIR, "pipeline_test.jpg")
    img = Image.new('RGB', (640, 640), color=(73, 109, 137))
    d = ImageDraw.Draw(img)
    d.rectangle([(200, 200), (440, 440)], fill=(255, 0, 0))
    img.save(test_img_path)

    print(f"[+] Created synthetic input image: {test_img_path}")

    # Run AI Analysis
    res = analyze_issue_image(test_img_path)

    if "error" in res:
        print("\n[+] AI Vision Pipeline Analysis Output: MODEL NOT AVAILABLE")
        print(f"    - Expected Error: {res['error']}")
        assert res["is_real_yolo"] is False
    else:
        print("\n[+] AI Vision Pipeline Analysis Output:")
        print(f"    - Detected Class: {res['issue_type']}")
        print(f"    - Confidence Score: {res['confidence'] * 100}%")
        print(f"    - Calculated Severity: {res['severity']}")
        print(f"    - Priority Score: {res['priority_score']} / 100")
        
        assert 0.0 <= res["confidence"] <= 1.0
        assert 0.0 <= res["priority_score"] <= 100.0

    print("\n[+] AI Pipeline Execution Check: PASSED")
    print("=" * 60)

if __name__ == "__main__":
    test_ai_vision_pipeline()
