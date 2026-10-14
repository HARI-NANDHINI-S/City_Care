"""
CivicVision AI — Phase 2: YOLO-First Detection Arbitration Regression Test Suite
=================================================================================

Comprehensive, isolated regression tests covering all 10 mandated scenarios for
safe model-result arbitration:
1. Valid YOLO detection is returned when no classification result exists.
2. YOLO detections remain selected results when classification confidence is higher.
3. Multiple valid YOLO detections are preserved with their bounding boxes.
4. Classification is not treated as a bounding-box detection (bounding_boxes=[], bounding_box=None).
5. Classification is ignored when the feature flag is disabled, even if checkpoint exists.
6. Classification cannot run when required runtime weights are missing.
7. Unsupported classifier classes remain filtered out.
8. Manual reporting continues to work as fallback when automated inference is unavailable.
9. Empty, malformed, or invalid model outputs are handled safely without crashing.
10. Existing 12-category registry mappings and API response schemas remain unchanged.

Uses temporary in-memory/ephemeral SQLite databases and lightweight mocks.
Does NOT access or mutate production civicsense.db, civicvision.db, or live weights.
"""

import os
import sys
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
from app.core.config import settings
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
    """Controlled mock YOLO adapter for testing arbitration."""
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
            "execution_time_ms": 12.0,
            "error_message": None
        }


class MockClassificationAdapter(BaseDefectModelAdapter):
    """Controlled mock classifier adapter for testing arbitration."""
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
            "execution_time_ms": 8.0,
            "error_message": None
        }


class TestYOLOFirstArbitration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Setup isolated ephemeral directory and SQLite database
        cls.temp_dir = tempfile.mkdtemp(prefix="civicvision_arbitration_test_")
        cls.test_db_path = os.path.join(cls.temp_dir, "arbitration_test.db")
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
            full_name="Arbitration Tester",
            email="citizen.arbitration@civicvision.ai",
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

        res_c = cls.client.post("/api/v1/auth/login", json={"email": "citizen.arbitration@civicvision.ai", "password": "TestPass@123"})
        cls.citizen_token = res_c.json()["access_token"]
        cls.citizen_headers = {"Authorization": f"Bearer {cls.citizen_token}"}

        # Create dummy test image fixture
        cls.test_img_path = os.path.join(cls.temp_dir, "arbitration_dummy.jpg")
        Image.new("RGB", (640, 480), color="gray").save(cls.test_img_path)

        # Preserve original registry adapters
        cls._orig_adapters = dict(model_registry._adapters)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        model_registry._adapters = cls._orig_adapters
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def tearDown(self):
        # Restore model registry after each test
        model_registry._adapters = dict(self._orig_adapters)

    # -------------------------------------------------------------------------
    # Scenario 1: A valid YOLO detection is returned when no classification result exists
    # -------------------------------------------------------------------------
    def test_01_valid_yolo_detection_returned_when_no_classification(self):
        yolo_det = {
            "class": "Pothole",
            "raw_class": "D40",
            "confidence": 0.75,
            "bounding_box": [50, 50, 200, 200]
        }
        mock_yolo = MockYOLOAdapter(detections=[yolo_det])
        mock_cls = MockClassificationAdapter(detections=[], available=False)

        model_registry._adapters = {
            mock_yolo.model_id: mock_yolo,
            mock_cls.model_id: mock_cls
        }

        result = analyze_issue_image(self.test_img_path)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["issue_type"], "Pothole")
        self.assertAlmostEqual(result["confidence"], 0.75, places=2)
        self.assertTrue(result["is_real_yolo"])
        self.assertEqual(len(result["bounding_boxes"]), 1)
        self.assertEqual(result["count"], 1)
        self.assertGreater(result["defect_area_ratio"], 0.0)
        self.assertEqual(result["recommended_department_code"], "DEPT_PWD")
        self.assertEqual(result["detected_defects"][0]["category"], "Pothole")
        self.assertEqual(result["detected_defects"][0]["bounding_box"], [50, 50, 150, 150])

    # -------------------------------------------------------------------------
    # Scenario 2: YOLO detections remain selected results when classification confidence is higher
    # -------------------------------------------------------------------------
    def test_02_yolo_precedence_over_higher_confidence_classification(self):
        """
        Crucial Rule 1 & 3: Localized YOLO detection (Pothole at 0.65) must take strict precedence
        over whole-image classification (Damaged Road Surface at 0.95).
        """
        yolo_det = {
            "class": "Pothole",
            "raw_class": "D40",
            "confidence": 0.65,
            "bounding_box": [30, 40, 120, 150]
        }
        cls_det = {
            "class": "Damaged Road Surface",
            "raw_class": "broken_edges",
            "confidence": 0.95,
            "bounding_box": None
        }
        mock_yolo = MockYOLOAdapter(detections=[yolo_det])
        mock_cls = MockClassificationAdapter(detections=[cls_det], available=True, enabled=True)

        model_registry._adapters = {
            mock_yolo.model_id: mock_yolo,
            mock_cls.model_id: mock_cls
        }

        result = analyze_issue_image(self.test_img_path)
        self.assertEqual(result["status"], "success")
        # Strict arbitration assertion: Pothole (0.65) must win over Damaged Road Surface (0.95)
        self.assertEqual(result["issue_type"], "Pothole", "YOLO localized detection MUST take precedence over classifier!")
        self.assertAlmostEqual(result["confidence"], 0.65, places=2)
        self.assertTrue(result["is_real_yolo"])
        self.assertEqual(result["recommended_department_code"], "DEPT_PWD")
        self.assertEqual(len(result["bounding_boxes"]), 1)
        self.assertEqual(result["bounding_boxes"][0]["class"], "Pothole")

        # Multi-defect details: Pothole has bounding box; classification is recorded as secondary scene context
        det_categories = [d["category"] for d in result["detected_defects"]]
        self.assertIn("Pothole", det_categories)
        self.assertIn("Damaged Road Surface", det_categories)
        pothole_defect = next(d for d in result["detected_defects"] if d["category"] == "Pothole")
        self.assertIsNotNone(pothole_defect["bounding_box"])
        cls_defect = next(d for d in result["detected_defects"] if d["category"] == "Damaged Road Surface")
        self.assertIsNone(cls_defect["bounding_box"], "Classification must not have a bounding box")

    # -------------------------------------------------------------------------
    # Scenario 3: Multiple valid YOLO detections are preserved
    # -------------------------------------------------------------------------
    def test_03_multiple_valid_yolo_detections_preserved(self):
        yolo_dets = [
            {"class": "Pothole", "raw_class": "D40", "confidence": 0.70, "bounding_box": [10, 10, 60, 60]},
            {"class": "Alligator Crack", "raw_class": "D20", "confidence": 0.82, "bounding_box": [100, 100, 250, 200]},
            {"class": "Longitudinal Crack", "raw_class": "D00", "confidence": 0.60, "bounding_box": [300, 50, 320, 300]}
        ]
        cls_det = {
            "class": "Damaged Road Surface",
            "raw_class": "broken_edges",
            "confidence": 0.99,
            "bounding_box": None
        }
        mock_yolo = MockYOLOAdapter(detections=yolo_dets)
        mock_cls = MockClassificationAdapter(detections=[cls_det], available=True, enabled=True)

        model_registry._adapters = {
            mock_yolo.model_id: mock_yolo,
            mock_cls.model_id: mock_cls
        }

        result = analyze_issue_image(self.test_img_path)
        self.assertEqual(result["status"], "success")
        # Winner among YOLO is Alligator Crack (0.82), NOT classifier (0.99)
        self.assertEqual(result["issue_type"], "Alligator Crack")
        self.assertAlmostEqual(result["confidence"], 0.82, places=2)
        self.assertTrue(result["is_real_yolo"])
        # All 3 YOLO bounding boxes preserved
        self.assertEqual(len(result["bounding_boxes"]), 3)
        self.assertEqual(result["count"], 3)
        classes_in_boxes = [b["class"] for b in result["bounding_boxes"]]
        self.assertIn("Pothole", classes_in_boxes)
        self.assertIn("Alligator Crack", classes_in_boxes)
        self.assertIn("Longitudinal Crack", classes_in_boxes)

    # -------------------------------------------------------------------------
    # Scenario 4: Classification is not treated as a bounding-box detection
    # -------------------------------------------------------------------------
    def test_04_classification_not_treated_as_bounding_box_detection(self):
        """
        When zero YOLO detections exist and classifier is active:
        Classification result must have bounding_boxes=[], bounding_box=None, defect_area_ratio=0.0.
        """
        cls_det = {
            "class": "Waterlogging",
            "raw_class": "waterlogged_roads",
            "confidence": 0.88,
            "bounding_box": None
        }
        mock_yolo = MockYOLOAdapter(detections=[])
        mock_cls = MockClassificationAdapter(detections=[cls_det], available=True, enabled=True)

        model_registry._adapters = {
            mock_yolo.model_id: mock_yolo,
            mock_cls.model_id: mock_cls
        }

        result = analyze_issue_image(self.test_img_path)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["issue_type"], "Waterlogging")
        self.assertAlmostEqual(result["confidence"], 0.88, places=2)
        self.assertFalse(result["is_real_yolo"], "Must not be attributed to YOLO")
        # Strict spatial truthfulness
        self.assertEqual(result["bounding_boxes"], [], "Classification must have empty bounding_boxes")
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["defect_area_ratio"], 0.0)
        self.assertIsNone(result["detected_defects"][0]["bounding_box"], "bounding_box MUST be None")
        self.assertEqual(result["recommended_department_code"], "DEPT_DRAIN")

    # -------------------------------------------------------------------------
    # Scenario 5: Classification is ignored when the feature flag is disabled
    # -------------------------------------------------------------------------
    def test_05_classification_ignored_when_feature_flag_disabled(self):
        """
        Even if a checkpoint file exists on disk, when ENABLE_IRDID_CLASSIFIER=False,
        the classifier adapter must remain unavailable and ignored.
        """
        dummy_weights = Path(self.temp_dir) / "irdid_test_weights.pt"
        dummy_weights.write_bytes(b"dummy binary weights")

        real_adapter = IRDIDClassificationAdapter(weights_path=dummy_weights, enabled=False)
        self.assertFalse(real_adapter.is_available)

        # In model registry, unavailable adapters are not active
        mock_yolo = MockYOLOAdapter(detections=[])
        model_registry._adapters = {
            mock_yolo.model_id: mock_yolo,
            real_adapter.model_id: real_adapter
        }

        active = model_registry.get_all_active_adapters()
        self.assertNotIn(real_adapter, active)

        result = analyze_issue_image(self.test_img_path)
        self.assertEqual(result["status"], "no_detection")
        self.assertIsNone(result["issue_type"])

    # -------------------------------------------------------------------------
    # Scenario 6: Classification cannot run when required runtime weights are missing
    # -------------------------------------------------------------------------
    def test_06_classification_cannot_run_when_weights_missing(self):
        non_existent_weights = Path(self.temp_dir) / "does_not_exist_weights.pt"
        self.assertFalse(non_existent_weights.exists())

        adapter = IRDIDClassificationAdapter(weights_path=non_existent_weights, enabled=True)
        self.assertFalse(adapter.is_available)

        infer_res = adapter.infer(self.test_img_path)
        self.assertEqual(infer_res["status"], "unsupported")
        self.assertEqual(infer_res["raw_detections"], [])
        self.assertIn("not found", infer_res["error_message"])

    # -------------------------------------------------------------------------
    # Scenario 7: Unsupported classifier classes remain filtered
    # -------------------------------------------------------------------------
    def test_07_unsupported_classifier_classes_filtered(self):
        """
        IRDID adapter must filter out classes outside ['Damaged Road Surface', 'Waterlogging'].
        """
        adapter = IRDIDClassificationAdapter(weights_path=Path(self.test_img_path), enabled=True)

        mock_probs = MagicMock()
        mock_probs.top1 = 0
        mock_probs.top1conf = MagicMock()
        mock_probs.top1conf.item.return_value = 0.95

        mock_result = MagicMock()
        mock_result.probs = mock_probs
        mock_result.names = {0: "open_manholes"}  # Out of active scope

        adapter._model = MagicMock(return_value=[mock_result])
        adapter._is_loaded = True

        infer_res = adapter.infer(self.test_img_path)
        self.assertEqual(infer_res["status"], "success")
        self.assertEqual(infer_res["raw_detections"], [], "Unsupported class 'open_manholes' must be filtered")

    # -------------------------------------------------------------------------
    # Scenario 8: Manual reporting continues to work when automated inference is unavailable
    # -------------------------------------------------------------------------
    def test_08_manual_reporting_fallback_when_inference_unavailable(self):
        # When automated inference returns no_detection, citizen manual submission operates cleanly
        payload = {
            "title": "Severe Pothole Report via Manual Form",
            "description": "Observed large cavity on arterial road",
            "issue_type": "Pothole",
            "latitude": 13.0827,
            "longitude": 80.2707,
            "address": "Anna Salai, Chennai",
            "original_image_url": "/uploads/original/manual_pothole.jpg",
            "ai_confidence": 0.0,
            "severity": "HIGH",
            "priority_score": 75.0,
            "bounding_box_json": "[]",
            "ai_analysis_status": "MANUAL_OR_UNAVAILABLE"
        }
        res = self.client.post("/api/v1/issues", json=payload, headers=self.citizen_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "REPORTED")
        self.assertEqual(data["issue_type"], "Pothole")
        self.assertEqual(data["department"]["code"], "DEPT_PWD")
        self.assertEqual(data["ai_analysis_status"], "MANUAL_OR_UNAVAILABLE")

    # -------------------------------------------------------------------------
    # Scenario 9: Empty, malformed, or invalid model outputs are handled safely
    # -------------------------------------------------------------------------
    def test_09_empty_malformed_invalid_model_outputs_handled_safely(self):
        class MalformedAdapter(BaseDefectModelAdapter):
            @property
            def model_id(self):
                return "malformed-adapter-v1"

            @property
            def supported_categories(self):
                return ["Pothole"]

            @property
            def is_available(self):
                return True

            def infer(self, image_path: str):
                return {
                    "status": "success",
                    "model_id": self.model_id,
                    "raw_detections": [
                        None,                                                      # None detection
                        {},                                                        # Empty dict
                        "not_a_dict",                                              # String item
                        {"class": "Pothole", "confidence": "high"},               # String confidence
                        {"class": "Pothole", "confidence": -0.5},                  # Negative confidence
                        {"class": "Pothole", "confidence": 1.5},                   # >1.0 confidence
                        {"class": "Pothole", "confidence": 0.8, "bounding_box": "invalid_box"}, # String box
                        {"class": "Pothole", "confidence": 0.8, "bounding_box": [100, 100, 50, 50]}, # Inverted coords (x2 < x1)
                        {"class": "Pothole", "confidence": 0.8, "bounding_box": [-10, 0, 50, 50]}, # Negative coords
                        {"confidence": 0.85},                                      # Missing class
                        {"class": "NonExistentDefectXYZ", "confidence": 0.90},     # Unknown category
                        {"class": "Pothole", "confidence": 0.77, "bounding_box": [10, 10, 80, 80]} # Valid!
                    ],
                    "execution_time_ms": 10.0,
                    "error_message": None
                }

        malformed_adapter = MalformedAdapter()
        model_registry._adapters = {malformed_adapter.model_id: malformed_adapter}

        # Should execute safely without uncaught exceptions and extract only the 1 valid detection
        result = analyze_issue_image(self.test_img_path)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["issue_type"], "Pothole")
        self.assertAlmostEqual(result["confidence"], 0.77, places=2)
        self.assertEqual(len(result["bounding_boxes"]), 1)
        self.assertEqual(result["bounding_boxes"][0]["x"], 10)
        self.assertEqual(result["bounding_boxes"][0]["y"], 10)
        self.assertEqual(result["bounding_boxes"][0]["width"], 70)
        self.assertEqual(result["bounding_boxes"][0]["height"], 70)

    # -------------------------------------------------------------------------
    # Scenario 10: Existing 12-category registry mappings and API response schemas remain unchanged
    # -------------------------------------------------------------------------
    def test_10_twelve_category_registry_and_api_schema_unchanged(self):
        # 1. Active 12 categories intact
        self.assertEqual(len(ACTIVE_12_CATEGORIES), 12)
        expected_12 = {
            "Pothole", "Longitudinal Crack", "Transverse Crack", "Alligator Crack", "Damaged Road Surface",
            "Garbage Accumulation", "Illegal Dumping", "Overflowing Garbage Bins",
            "Blocked Drains", "Overflowing Drains", "Waterlogging", "Damaged Drainage Covers"
        }
        self.assertEqual(set(ACTIVE_12_CATEGORIES), expected_12)

        # 2. Registry specifications intact
        for cat in expected_12:
            spec = get_category_spec(cat)
            self.assertIsNotNone(spec)
            self.assertIn("domain", spec)
            self.assertIn("model_type", spec)
            self.assertIn("default_dept_code", spec)
            self.assertIn("confidence_threshold", spec)

        # 3. Quarantined categories outside active scope
        self.assertFalse(get_category_spec("Open Manhole")["is_active_scope"])
        self.assertFalse(get_category_spec("Road Damage")["is_active_scope"])

        # 4. API response schema exact keys verification
        yolo_det = {
            "class": "Pothole",
            "raw_class": "D40",
            "confidence": 0.80,
            "bounding_box": [10, 10, 60, 60]
        }
        mock_yolo = MockYOLOAdapter(detections=[yolo_det])
        model_registry._adapters = {mock_yolo.model_id: mock_yolo}

        result = analyze_issue_image(self.test_img_path)
        expected_keys = {
            "status", "issue_type", "confidence", "severity", "priority_score",
            "recommended_department", "recommended_department_code", "bounding_boxes",
            "detected_defects", "defect_area_ratio", "annotated_image_filename",
            "original_image_filename", "is_real_yolo", "count", "model_provenance"
        }
        self.assertEqual(set(result.keys()), expected_keys)

        # Verify no_detection response schema
        model_registry._adapters = {mock_yolo.model_id: MockYOLOAdapter(detections=[])}
        no_det_result = analyze_issue_image(self.test_img_path)
        self.assertEqual(no_det_result["status"], "no_detection")
        expected_no_det_keys = {
            "status", "message", "issue_type", "confidence", "severity", "priority_score",
            "recommended_department", "recommended_department_code", "bounding_boxes",
            "detected_defects", "defect_area_ratio", "annotated_image_filename",
            "original_image_filename", "is_real_yolo", "count", "model_provenance"
        }
        self.assertEqual(set(no_det_result.keys()), expected_no_det_keys)


if __name__ == "__main__":
    unittest.main()
