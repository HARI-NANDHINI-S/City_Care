"""
CivicVision AI — Phase 3: Confidence Calibration & Safe Filtering Regression Tests
===================================================================================

Comprehensive test suite verifying evidence-based confidence filtering:
1. Configuration defaults and fail-safe parsing for YOLO and IRDID thresholds.
2. Boundary testing immediately below, at, and above thresholds.
3. Non-finite, NaN, infinite, and malformed confidence filtering.
4. Dynamic settings threshold configuration.
5. Inactive classifier settings when ENABLE_IRDID_CLASSIFIER=False.
6. Missing classifier weights and unsupported class handling.
7. Manual-reporting fallback when predictions are filtered below threshold.
8. Preservation of YOLO-first spatial arbitration, bounding boxes, and API schemas.
9. Integrity of 12 active category specifications.
"""

import os
import sys
import math
import json
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import MagicMock
from PIL import Image

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings, Settings
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.issue import Issue, IssueStatus, IssueType, SeverityLevel
from app.core.security import get_password_hash
from app.core.defect_registry import DEFECT_REGISTRY, ACTIVE_12_CATEGORIES, get_category_spec
from app.services.models.base_adapter import BaseDefectModelAdapter
from app.services.models.classification_adapter import IRDIDClassificationAdapter
from app.services.models.registry import model_registry
from app.services.ai_service import analyze_issue_image


class MockYOLOAdapter(BaseDefectModelAdapter):
    def __init__(self, detections=None):
        self._detections = detections or []

    @property
    def model_id(self) -> str:
        return "yolov8-rdd2020-india-v1"

    @property
    def supported_categories(self):
        return ["Pothole", "Longitudinal Crack", "Transverse Crack", "Alligator Crack"]

    @property
    def is_available(self) -> bool:
        return True

    def infer(self, image_path: str):
        return {
            "status": "success",
            "model_id": self.model_id,
            "raw_detections": list(self._detections),
            "execution_time_ms": 11.0,
            "error_message": None
        }


class MockClassificationAdapter(BaseDefectModelAdapter):
    def __init__(self, detections=None, available=True, enabled=True):
        self._detections = detections or []
        self._available = available
        self._enabled = enabled

    @property
    def model_id(self) -> str:
        return "irdid-classifier-candidate"

    @property
    def supported_categories(self):
        return ["Damaged Road Surface", "Waterlogging"]

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    @property
    def is_available(self) -> bool:
        return self._available

    def infer(self, image_path: str):
        if not self._available:
            return {
                "status": "unsupported",
                "model_id": self.model_id,
                "raw_detections": [],
                "execution_time_ms": 0.0,
                "error_message": "Classifier unavailable"
            }
        return {
            "status": "success",
            "model_id": self.model_id,
            "raw_detections": list(self._detections),
            "execution_time_ms": 9.0,
            "error_message": None
        }


class TestConfidenceCalibrationFiltering(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp(prefix="civicvision_calib_test_")
        cls.test_db_path = os.path.join(cls.temp_dir, "calib_test.db")
        cls.test_db_url = f"sqlite:///{cls.test_db_path}"

        assert "civicsense.db" not in cls.test_db_url.lower()

        cls.engine = create_engine(cls.test_db_url, connect_args={"check_same_thread": False})
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

        session = cls.SessionLocal()
        cls.dept_pwd = Department(name="Road & Public Works Department", code="DEPT_PWD", description="Roads")
        cls.dept_san = Department(name="Waste Management & Sanitation Dept", code="DEPT_SAN", description="Sanitation")
        cls.dept_drain = Department(name="Stormwater Drainage Dept", code="DEPT_DRAIN", description="Drainage")
        session.add_all([cls.dept_pwd, cls.dept_san, cls.dept_drain])
        session.commit()

        cls.citizen = User(
            full_name="Calibration Tester",
            email="citizen.calib@civicvision.ai",
            hashed_password=get_password_hash("TestPass@123"),
            role=UserRole.CITIZEN
        )
        session.add(cls.citizen)
        session.commit()
        session.close()

        def override_get_db():
            db = cls.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

        res_c = cls.client.post("/api/v1/auth/login", json={"email": "citizen.calib@civicvision.ai", "password": "TestPass@123"})
        cls.citizen_token = res_c.json()["access_token"]
        cls.citizen_headers = {"Authorization": f"Bearer {cls.citizen_token}"}

        # Create dummy test image fixture
        cls.test_img_path = os.path.join(cls.temp_dir, "calib_dummy.jpg")
        Image.new("RGB", (640, 480), color="gray").save(cls.test_img_path)

        cls._orig_adapters = dict(model_registry._adapters)
        cls._orig_yolo_thresh = settings.YOLO_CONFIDENCE_THRESHOLD
        cls._orig_irdid_thresh = settings.IRDID_CLASSIFIER_THRESHOLD

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        model_registry._adapters = cls._orig_adapters
        settings.YOLO_CONFIDENCE_THRESHOLD = cls._orig_yolo_thresh
        settings.IRDID_CLASSIFIER_THRESHOLD = cls._orig_irdid_thresh
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def tearDown(self):
        model_registry._adapters = dict(self._orig_adapters)
        settings.YOLO_CONFIDENCE_THRESHOLD = self._orig_yolo_thresh
        settings.IRDID_CLASSIFIER_THRESHOLD = self._orig_irdid_thresh

    # -------------------------------------------------------------------------
    # Test 1: Configuration Defaults & Fail-Safe Validation
    # -------------------------------------------------------------------------
    def test_01_configuration_defaults_and_fail_safe_parsing(self):
        # Default settings verification
        self.assertEqual(settings.YOLO_CONFIDENCE_THRESHOLD, 0.25)
        self.assertEqual(settings.IRDID_CLASSIFIER_THRESHOLD, 0.30)
        self.assertFalse(settings.ENABLE_IRDID_CLASSIFIER)

        # Valid custom values
        s_custom = Settings(YOLO_CONFIDENCE_THRESHOLD=0.35, IRDID_CLASSIFIER_THRESHOLD=0.45)
        self.assertAlmostEqual(s_custom.YOLO_CONFIDENCE_THRESHOLD, 0.35)
        self.assertAlmostEqual(s_custom.IRDID_CLASSIFIER_THRESHOLD, 0.45)

        # String numeric values
        s_str = Settings(YOLO_CONFIDENCE_THRESHOLD="0.40", IRDID_CLASSIFIER_THRESHOLD="0.50")
        self.assertAlmostEqual(s_str.YOLO_CONFIDENCE_THRESHOLD, 0.40)
        self.assertAlmostEqual(s_str.IRDID_CLASSIFIER_THRESHOLD, 0.50)

        # Fail-safe fallback on invalid string
        s_invalid_str = Settings(YOLO_CONFIDENCE_THRESHOLD="uncalibrated_string", IRDID_CLASSIFIER_THRESHOLD="bad_val")
        self.assertEqual(s_invalid_str.YOLO_CONFIDENCE_THRESHOLD, 0.25)
        self.assertEqual(s_invalid_str.IRDID_CLASSIFIER_THRESHOLD, 0.30)

        # Fail-safe fallback on NaN and inf
        s_nan = Settings(YOLO_CONFIDENCE_THRESHOLD=float("nan"), IRDID_CLASSIFIER_THRESHOLD=float("inf"))
        self.assertEqual(s_nan.YOLO_CONFIDENCE_THRESHOLD, 0.25)
        self.assertEqual(s_nan.IRDID_CLASSIFIER_THRESHOLD, 0.30)

        # Fail-safe fallback on out-of-range (< 0.05 or > 0.95)
        s_oor_low = Settings(YOLO_CONFIDENCE_THRESHOLD=0.01, IRDID_CLASSIFIER_THRESHOLD=0.02)
        self.assertEqual(s_oor_low.YOLO_CONFIDENCE_THRESHOLD, 0.25)
        self.assertEqual(s_oor_low.IRDID_CLASSIFIER_THRESHOLD, 0.30)

        s_oor_high = Settings(YOLO_CONFIDENCE_THRESHOLD=0.99, IRDID_CLASSIFIER_THRESHOLD=1.5)
        self.assertEqual(s_oor_high.YOLO_CONFIDENCE_THRESHOLD, 0.25)
        self.assertEqual(s_oor_high.IRDID_CLASSIFIER_THRESHOLD, 0.30)

    # -------------------------------------------------------------------------
    # Test 2: YOLO Threshold Boundary Testing (Below, At, Above)
    # -------------------------------------------------------------------------
    def test_02_yolo_threshold_boundary_filtering(self):
        settings.YOLO_CONFIDENCE_THRESHOLD = 0.25

        # 1. Immediately below threshold (0.2499) -> must be filtered out
        det_below = {"class": "Pothole", "raw_class": "D40", "confidence": 0.2499, "bounding_box": [10, 10, 50, 50]}
        model_registry._adapters = {"yolov8-rdd2020-india-v1": MockYOLOAdapter([det_below])}
        res_below = analyze_issue_image(self.test_img_path)
        self.assertEqual(res_below["status"], "no_detection")
        self.assertEqual(res_below["bounding_boxes"], [])

        # 2. Exactly at threshold (0.2500) -> must be accepted
        det_at = {"class": "Pothole", "raw_class": "D40", "confidence": 0.2500, "bounding_box": [10, 10, 50, 50]}
        model_registry._adapters = {"yolov8-rdd2020-india-v1": MockYOLOAdapter([det_at])}
        res_at = analyze_issue_image(self.test_img_path)
        self.assertEqual(res_at["status"], "success")
        self.assertEqual(res_at["issue_type"], "Pothole")
        self.assertEqual(len(res_at["bounding_boxes"]), 1)

        # 3. Immediately above threshold (0.2501) -> must be accepted
        det_above = {"class": "Pothole", "raw_class": "D40", "confidence": 0.2501, "bounding_box": [10, 10, 50, 50]}
        model_registry._adapters = {"yolov8-rdd2020-india-v1": MockYOLOAdapter([det_above])}
        res_above = analyze_issue_image(self.test_img_path)
        self.assertEqual(res_above["status"], "success")
        self.assertEqual(res_above["issue_type"], "Pothole")
        self.assertEqual(len(res_above["bounding_boxes"]), 1)

    # -------------------------------------------------------------------------
    # Test 3: Classifier Threshold Boundary Testing (Below, At, Above)
    # -------------------------------------------------------------------------
    def test_03_classifier_threshold_boundary_filtering(self):
        settings.IRDID_CLASSIFIER_THRESHOLD = 0.30

        # 1. Immediately below threshold (0.2999) -> filtered out
        cls_below = {"class": "Damaged Road Surface", "raw_class": "broken_edges", "confidence": 0.2999, "bounding_box": None}
        mock_cls = MockClassificationAdapter([cls_below], available=True, enabled=True)
        model_registry._adapters = {mock_cls.model_id: mock_cls}
        res_below = analyze_issue_image(self.test_img_path)
        self.assertEqual(res_below["status"], "no_detection")

        # 2. Exactly at threshold (0.3000) -> accepted
        cls_at = {"class": "Damaged Road Surface", "raw_class": "broken_edges", "confidence": 0.3000, "bounding_box": None}
        mock_cls = MockClassificationAdapter([cls_at], available=True, enabled=True)
        model_registry._adapters = {mock_cls.model_id: mock_cls}
        res_at = analyze_issue_image(self.test_img_path)
        self.assertEqual(res_at["status"], "success")
        self.assertEqual(res_at["issue_type"], "Damaged Road Surface")
        self.assertEqual(res_at["bounding_boxes"], [])

        # 3. Immediately above threshold (0.3001) -> accepted
        cls_above = {"class": "Damaged Road Surface", "raw_class": "broken_edges", "confidence": 0.3001, "bounding_box": None}
        mock_cls = MockClassificationAdapter([cls_above], available=True, enabled=True)
        model_registry._adapters = {mock_cls.model_id: mock_cls}
        res_above = analyze_issue_image(self.test_img_path)
        self.assertEqual(res_above["status"], "success")
        self.assertEqual(res_above["issue_type"], "Damaged Road Surface")

    # -------------------------------------------------------------------------
    # Test 4: Invalid, Missing, and Non-Finite Confidence Filtering
    # -------------------------------------------------------------------------
    def test_04_invalid_missing_nonfinite_confidence_filtered_safely(self):
        malformed_detections = [
            {"class": "Pothole", "confidence": float("nan"), "bounding_box": [10, 10, 50, 50]},
            {"class": "Pothole", "confidence": float("inf"), "bounding_box": [10, 10, 50, 50]},
            {"class": "Pothole", "confidence": -float("inf"), "bounding_box": [10, 10, 50, 50]},
            {"class": "Pothole", "confidence": None, "bounding_box": [10, 10, 50, 50]},
            {"class": "Pothole", "confidence": "high_confidence", "bounding_box": [10, 10, 50, 50]},
            {"class": "Pothole", "confidence": -0.25, "bounding_box": [10, 10, 50, 50]},
            {"class": "Pothole", "confidence": 1.25, "bounding_box": [10, 10, 50, 50]},
            # Valid detection that should survive
            {"class": "Pothole", "confidence": 0.75, "bounding_box": [20, 20, 80, 80]}
        ]
        mock_yolo = MockYOLOAdapter(malformed_detections)
        model_registry._adapters = {mock_yolo.model_id: mock_yolo}

        result = analyze_issue_image(self.test_img_path)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["issue_type"], "Pothole")
        self.assertAlmostEqual(result["confidence"], 0.75, places=2)
        # Only the 1 valid detection survived
        self.assertEqual(len(result["bounding_boxes"]), 1)
        self.assertEqual(result["count"], 1)

    # -------------------------------------------------------------------------
    # Test 5: Dynamic Settings Threshold Configuration
    # -------------------------------------------------------------------------
    def test_05_dynamic_settings_threshold_configuration(self):
        # Override YOLO threshold to 0.50
        settings.YOLO_CONFIDENCE_THRESHOLD = 0.50

        det1 = {"class": "Pothole", "raw_class": "D40", "confidence": 0.40, "bounding_box": [10, 10, 50, 50]}
        det2 = {"class": "Alligator Crack", "raw_class": "D20", "confidence": 0.65, "bounding_box": [60, 60, 120, 120]}

        model_registry._adapters = {"yolov8-rdd2020-india-v1": MockYOLOAdapter([det1, det2])}
        result = analyze_issue_image(self.test_img_path)

        self.assertEqual(result["status"], "success")
        # det1 (0.40) was filtered out by 0.50 threshold; det2 (0.65) was accepted
        self.assertEqual(result["issue_type"], "Alligator Crack")
        self.assertAlmostEqual(result["confidence"], 0.65, places=2)
        self.assertEqual(len(result["bounding_boxes"]), 1)
        self.assertEqual(result["bounding_boxes"][0]["class"], "Alligator Crack")

    # -------------------------------------------------------------------------
    # Test 6: Inactive Classifier Settings when Disabled
    # -------------------------------------------------------------------------
    def test_06_inactive_classifier_settings_when_disabled(self):
        """
        When ENABLE_IRDID_CLASSIFIER=False, classifier settings are dormant
        and the classifier produces no predictions regardless of threshold.
        """
        self.assertFalse(settings.ENABLE_IRDID_CLASSIFIER)

        real_adapter = IRDIDClassificationAdapter(enabled=False)
        self.assertFalse(real_adapter.is_available)

        model_registry._adapters = {
            "yolov8-rdd2020-india-v1": MockYOLOAdapter([]),
            real_adapter.model_id: real_adapter
        }

        result = analyze_issue_image(self.test_img_path)
        self.assertEqual(result["status"], "no_detection")
        self.assertNotIn("irdid-classifier-candidate", [a.model_id for a in model_registry.get_all_active_adapters()])

    # -------------------------------------------------------------------------
    # Test 7: Missing Classifier Weights Handling
    # -------------------------------------------------------------------------
    def test_07_missing_classifier_weights(self):
        fake_path = Path(self.temp_dir) / "missing_model.pt"
        self.assertFalse(fake_path.exists())

        adapter = IRDIDClassificationAdapter(weights_path=fake_path, enabled=True)
        self.assertFalse(adapter.is_available)
        res = adapter.infer(self.test_img_path)
        self.assertEqual(res["status"], "unsupported")
        self.assertEqual(res["raw_detections"], [])

    # -------------------------------------------------------------------------
    # Test 8: Manual-Reporting Fallback when Predictions Filtered
    # -------------------------------------------------------------------------
    def test_08_manual_reporting_fallback_when_predictions_filtered(self):
        # When all detections are below threshold, pipeline returns no_detection
        weak_det = {"class": "Pothole", "raw_class": "D40", "confidence": 0.15, "bounding_box": [10, 10, 50, 50]}
        model_registry._adapters = {"yolov8-rdd2020-india-v1": MockYOLOAdapter([weak_det])}
        res_infer = analyze_issue_image(self.test_img_path)
        self.assertEqual(res_infer["status"], "no_detection")

        # Citizen submits manual report
        payload = {
            "title": "Subtle Road Crack Reported Manually",
            "description": "Citizen observed crack not detected with sufficient AI confidence",
            "issue_type": "Longitudinal Crack",
            "latitude": 13.0827,
            "longitude": 80.2707,
            "address": "Poonamallee High Road, Chennai",
            "original_image_url": "/uploads/original/crack_manual.jpg",
            "ai_confidence": 0.0,
            "severity": "MEDIUM",
            "priority_score": 55.0,
            "bounding_box_json": "[]",
            "ai_analysis_status": "MANUAL_OR_UNAVAILABLE"
        }
        res_post = self.client.post("/api/v1/issues", json=payload, headers=self.citizen_headers)
        self.assertEqual(res_post.status_code, 200)
        data = res_post.json()
        self.assertEqual(data["status"], "REPORTED")
        self.assertEqual(data["issue_type"], "Longitudinal Crack")
        self.assertEqual(data["department"]["code"], "DEPT_PWD")
        self.assertEqual(data["ai_analysis_status"], "MANUAL_OR_UNAVAILABLE")

    # -------------------------------------------------------------------------
    # Test 9: YOLO-First Arbitration with Confirmed Thresholds
    # -------------------------------------------------------------------------
    def test_09_yolo_first_arbitration_with_filtering(self):
        # YOLO detection above threshold (0.60 > 0.25)
        yolo_det = {"class": "Pothole", "raw_class": "D40", "confidence": 0.60, "bounding_box": [15, 15, 75, 75]}
        # Classifier prediction above threshold (0.90 > 0.30)
        cls_det = {"class": "Damaged Road Surface", "raw_class": "broken_edges", "confidence": 0.90, "bounding_box": None}

        mock_yolo = MockYOLOAdapter([yolo_det])
        mock_cls = MockClassificationAdapter([cls_det], available=True, enabled=True)
        model_registry._adapters = {mock_yolo.model_id: mock_yolo, mock_cls.model_id: mock_cls}

        result = analyze_issue_image(self.test_img_path)
        self.assertEqual(result["status"], "success")
        # YOLO must win
        self.assertEqual(result["issue_type"], "Pothole")
        self.assertAlmostEqual(result["confidence"], 0.60, places=2)
        self.assertTrue(result["is_real_yolo"])
        self.assertEqual(len(result["bounding_boxes"]), 1)
        self.assertEqual(result["bounding_boxes"][0]["class"], "Pothole")

    # -------------------------------------------------------------------------
    # Test 10: 12-Category Registry Specifications Intact
    # -------------------------------------------------------------------------
    def test_10_twelve_category_registry_specifications_intact(self):
        self.assertEqual(len(ACTIVE_12_CATEGORIES), 12)
        for cat_name in ACTIVE_12_CATEGORIES:
            spec = get_category_spec(cat_name)
            self.assertIsNotNone(spec)
            self.assertIn("domain", spec)
            self.assertIn("confidence_threshold", spec)
            self.assertGreater(spec["confidence_threshold"], 0.0)
            self.assertLess(spec["confidence_threshold"], 1.0)


if __name__ == "__main__":
    unittest.main()
