"""
CivicVision AI - Comprehensive Multi-Category Pipeline & System Test Suite
Uses temporary in-memory/ephemeral SQLite databases and temporary directories.
Does NOT modify or mutate production civicsense.db or live uploads.
"""
import os
import sys
import io
import json
import tempfile
import shutil
import unittest
from PIL import Image

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
from app.core.defect_registry import DEFECT_REGISTRY, DefectDomain, ModelReadinessStatus
from app.services.ai_service import analyze_issue_image
from app.services.routing_service import get_recommended_department_code, get_recommended_department_name
from app.services.priority_service import calculate_priority_score, get_severity_from_priority

class TestCivicVisionPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 1. Setup isolated ephemeral test database
        cls.temp_dir = tempfile.mkdtemp(prefix="civicvision_eval_")
        cls.test_db_path = os.path.join(cls.temp_dir, "eval_test.db")
        cls.test_db_url = f"sqlite:///{cls.test_db_path}"

        # Safety Guard
        assert "civicsense.db" not in cls.test_db_url.lower()

        cls.engine = create_engine(cls.test_db_url, connect_args={"check_same_thread": False})
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

        # Seed test departments and users
        session = cls.SessionLocal()
        cls.dept_pwd = Department(name="Road & Public Works Department", code="DEPT_PWD", description="Roads")
        cls.dept_san = Department(name="Waste Management & Sanitation Dept", code="DEPT_SAN", description="Sanitation")
        cls.dept_drain = Department(name="Stormwater Drainage Dept", code="DEPT_DRAIN", description="Drainage")
        session.add_all([cls.dept_pwd, cls.dept_san, cls.dept_drain])
        session.commit()

        cls.citizen = User(
            full_name="Citizen Tester",
            email="citizen.eval@civicvision.ai",
            hashed_password=get_password_hash("TestPass@123"),
            role=UserRole.CITIZEN
        )
        cls.admin = User(
            full_name="Admin Auditor",
            email="admin.eval@civicvision.ai",
            hashed_password=get_password_hash("TestPass@123"),
            role=UserRole.ADMIN
        )
        session.add_all([cls.citizen, cls.admin])
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

        # Logins
        res_c = cls.client.post("/api/v1/auth/login", json={"email": "citizen.eval@civicvision.ai", "password": "TestPass@123"})
        cls.citizen_token = res_c.json()["access_token"]
        cls.citizen_headers = {"Authorization": f"Bearer {cls.citizen_token}"}

        res_a = cls.client.post("/api/v1/auth/login", json={"email": "admin.eval@civicvision.ai", "password": "TestPass@123"})
        cls.admin_token = res_a.json()["access_token"]
        cls.admin_headers = {"Authorization": f"Bearer {cls.admin_token}"}

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_01_all_12_categories_in_registry(self):
        """Verify all 12 requested defect categories are formally registered with domain and routing."""
        expected_12 = [
            # Road
            "Pothole", "Longitudinal Crack", "Transverse Crack", "Alligator Crack", "Damaged Road Surface",
            # Sanitation
            "Garbage Accumulation", "Illegal Dumping", "Overflowing Garbage Bins",
            # Drainage
            "Blocked Drains", "Overflowing Drains", "Waterlogging", "Damaged Drainage Covers"
        ]
        for cat in expected_12:
            self.assertIn(cat, DEFECT_REGISTRY, f"Category '{cat}' missing from DEFECT_REGISTRY!")
            spec = DEFECT_REGISTRY[cat]
            self.assertIsNotNone(spec.get("default_dept_code"))
            self.assertIsNotNone(spec.get("readiness"))

    def test_02_department_routing_and_priority_matrix(self):
        """Test department routing and priority scoring across categories."""
        self.assertEqual(get_recommended_department_code("Pothole"), "DEPT_PWD")
        self.assertEqual(get_recommended_department_code("Garbage Accumulation"), "DEPT_SAN")
        self.assertEqual(get_recommended_department_code("Waterlogging"), "DEPT_DRAIN")
        self.assertEqual(get_recommended_department_code("Damaged Drainage Covers"), "DEPT_DRAIN")

        score_pothole = calculate_priority_score("Pothole", ai_confidence=0.85, defect_area_ratio=0.05)
        score_garbage = calculate_priority_score("Garbage Accumulation", ai_confidence=0.85, defect_area_ratio=0.05)
        # Higher risk defects should yield higher priority scores given identical geometry
        self.assertGreater(score_pothole, score_garbage)

    def test_03_genuine_yolo_inference_pothole(self):
        """Test actual YOLO model inference on Indian test image img0001.jpg."""
        test_img_path = os.path.abspath("Indian-Road-Damage-Infrastructure-Dataset/images/potholes/img0001.jpg")
        if os.path.exists(test_img_path):
            result = analyze_issue_image(test_img_path)
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["issue_type"], "Pothole")
            self.assertGreater(result["confidence"], 0.3)
            self.assertIn("yolov8-rdd2020-india-v1", result["model_provenance"])
            self.assertEqual(result["recommended_department_code"], "DEPT_PWD")

    def test_04_genuine_yolo_multi_detection(self):
        """Test multiple defect detections on Indian test image img0002.jpg."""
        test_img_path = os.path.abspath("Indian-Road-Damage-Infrastructure-Dataset/images/potholes/img0002.jpg")
        if os.path.exists(test_img_path):
            result = analyze_issue_image(test_img_path)
            self.assertEqual(result["status"], "success")
            self.assertGreaterEqual(len(result["detected_defects"]), 2)
            categories = [d["category"] for d in result["detected_defects"]]
            self.assertIn("Pothole", categories)
            self.assertIn("Alligator Crack", categories)

    def test_05_corrupt_or_invalid_image_handling(self):
        """Verify pipeline handles corrupted or non-image files safely without crashing."""
        corrupt_path = os.path.join(self.temp_dir, "corrupt.jpg")
        with open(corrupt_path, "wb") as f:
            f.write(b"NOT_A_REAL_IMAGE_DATA")

        result = analyze_issue_image(corrupt_path)
        self.assertEqual(result["status"], "analysis_failed")
        self.assertIn("Corrupt or invalid image", result["message"])

    def test_06_issue_creation_and_provenance_persistence(self):
        """Test report creation with multi-defect details, model provenance, and DB persistence."""
        payload = {
            "title": "Severe Pothole and Cracking on GST Road",
            "description": "Deep depression in asphalt",
            "issue_type": "Pothole",
            "latitude": 13.0827,
            "longitude": 80.2707,
            "address": "GST Road, Chennai",
            "original_image_url": "/uploads/original/test_orig.jpg",
            "annotated_image_url": "/uploads/annotated/test_annot.jpg",
            "ai_confidence": 0.88,
            "severity": "HIGH",
            "priority_score": 85.0,
            "bounding_box_json": json.dumps([{"class": "Pothole", "confidence": 0.88}]),
            "detected_defects_json": json.dumps([
                {"category": "Pothole", "confidence": 0.88},
                {"category": "Alligator Crack", "confidence": 0.54}
            ]),
            "model_provenance_json": json.dumps({"model_id": "yolov8-rdd2020-india-v1"}),
            "ai_analysis_status": "SUCCESS"
        }
        res = self.client.post("/api/v1/issues", json=payload, headers=self.citizen_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "AI_ANALYZED")
        self.assertEqual(data["issue_type"], "Pothole")
        self.assertIsNotNone(data["detected_defects_json"])

        issue_id = data["id"]
        # Verify municipal review and category correction
        verify_payload = {
            "verified_category": "Damaged Road Surface",
            "notes": "Field inspection notes large patch of raveling along with pothole."
        }
        res_verify = self.client.patch(f"/api/v1/issues/{issue_id}/verify-category", json=verify_payload, headers=self.admin_headers)
        self.assertEqual(res_verify.status_code, 200)
        verify_data = res_verify.json()
        self.assertEqual(verify_data["verified_category"], "Damaged Road Surface")

    def test_07_citizen_forbidden_to_verify_category(self):
        """Ensure RBAC blocks citizen users from verifying/modifying defect categories."""
        verify_payload = {"verified_category": "Damaged Road Surface"}
        res = self.client.patch("/api/v1/issues/1/verify-category", json=verify_payload, headers=self.citizen_headers)
        self.assertEqual(res.status_code, 403)

if __name__ == "__main__":
    unittest.main()
