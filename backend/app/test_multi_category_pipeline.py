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

    def test_08_categories_endpoint_12_active_and_capabilities(self):
        """Verify GET /api/v1/issues/categories returns exactly 12 active categories with capabilities."""
        res = self.client.get("/api/v1/issues/categories")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["total_active"], 12)
        active_names = [c["name"] for c in data["active_categories"]]
        self.assertEqual(len(active_names), 12)
        
        # Verify active 12
        expected_12 = [
            "Pothole", "Longitudinal Crack", "Transverse Crack", "Alligator Crack", "Damaged Road Surface",
            "Garbage Accumulation", "Illegal Dumping", "Overflowing Garbage Bins",
            "Blocked Drains", "Overflowing Drains", "Waterlogging", "Damaged Drainage Covers"
        ]
        self.assertEqual(sorted(active_names), sorted(expected_12))

        # Quarantine check: Open Manholes and Broken Streetlights must NOT be in active categories
        self.assertNotIn("Open Manhole", active_names)
        self.assertNotIn("Broken Streetlight", active_names)
        self.assertNotIn("Road Damage", active_names)

        # Capability check: each category has readiness and model_type
        for cat in data["active_categories"]:
            self.assertIn("readiness", cat)
            self.assertIn("readiness_label", cat)
            self.assertIn("model_type", cat)

    def test_09_capability_and_scope_distinctions(self):
        """Verify distinct semantics for manholes vs drainage covers and waterlogging classification."""
        from app.core.defect_registry import get_category_spec, ModelReadinessStatus
        
        # 1. Drainage cover vs Open Manhole distinction
        drainage_spec = get_category_spec("Damaged Drainage Covers")
        manhole_spec = get_category_spec("Open Manhole")
        self.assertNotEqual(drainage_spec["domain"], manhole_spec["domain"])
        self.assertEqual(drainage_spec["default_dept_code"], "DEPT_DRAIN")
        self.assertEqual(manhole_spec["default_dept_code"], "DEPT_SEW")
        self.assertTrue(drainage_spec["is_active_scope"])
        self.assertFalse(manhole_spec["is_active_scope"])

        # 2. Waterlogging whole-image classification vs localized detection
        water_spec = get_category_spec("Waterlogging")
        self.assertEqual(water_spec["model_type"], "image_classification")
        self.assertEqual(water_spec["readiness"], ModelReadinessStatus.IMAGE_CLASSIFICATION_ONLY)

        # 3. Transverse Crack has 9 test instances in RDD2020 India
        tc_spec = get_category_spec("Transverse Crack")
        self.assertIn("9 test instances", tc_spec["description"])

    def test_10_multi_domain_manual_reporting_and_routing(self):
        """Verify manual reporting across all 12 active categories routes to correct departments."""
        test_cases = [
            # Roads (5)
            ("Pothole", "DEPT_PWD"),
            ("Longitudinal Crack", "DEPT_PWD"),
            ("Transverse Crack", "DEPT_PWD"),
            ("Alligator Crack", "DEPT_PWD"),
            ("Damaged Road Surface", "DEPT_PWD"),
            # Sanitation (3)
            ("Garbage Accumulation", "DEPT_SAN"),
            ("Illegal Dumping", "DEPT_SAN"),
            ("Overflowing Garbage Bins", "DEPT_SAN"),
            # Drainage (4)
            ("Blocked Drains", "DEPT_DRAIN"),
            ("Overflowing Drains", "DEPT_DRAIN"),
            ("Waterlogging", "DEPT_DRAIN"),
            ("Damaged Drainage Covers", "DEPT_DRAIN"),
        ]
        self.assertEqual(len(test_cases), 12, "Must test exactly 12 active categories!")

        for category, expected_dept_code in test_cases:
            payload = {
                "title": f"Manual citizen report: {category}",
                "description": f"Citizen observed {category} requiring municipal attention.",
                "issue_type": category,
                "latitude": 13.0827,
                "longitude": 80.2707,
                "address": "Civic Area Sector 1",
                "original_image_url": "/uploads/original/manual_sample.jpg",
                "ai_confidence": 0.0,
                "severity": "MEDIUM",
                "priority_score": 50.0,
                "bounding_box_json": "[]",
                "ai_analysis_status": "MANUAL_OR_UNAVAILABLE"
            }
            res = self.client.post("/api/v1/issues", json=payload, headers=self.citizen_headers)
            self.assertEqual(res.status_code, 200, f"Failed creating report for {category}: {res.text}")
            data = res.json()
            self.assertEqual(data["status"], "REPORTED")
            self.assertEqual(data["issue_type"], category)
            self.assertIsNotNone(data["department"], f"No department routed for {category}")
            self.assertEqual(data["department"]["code"], expected_dept_code)

    def test_11_my_reports_and_details_retrieval(self):
        """Verify citizen can retrieve submitted reports via /my-reports and /issues/{id}."""
        # 1. Retrieve all citizen reports
        res_list = self.client.get("/api/v1/issues/my-reports", headers=self.citizen_headers)
        self.assertEqual(res_list.status_code, 200)
        reports = res_list.json()
        self.assertGreaterEqual(len(reports), 12)

        # 2. Filter by category
        res_filtered = self.client.get("/api/v1/issues/my-reports?category=Waterlogging", headers=self.citizen_headers)
        self.assertEqual(res_filtered.status_code, 200)
        water_reports = res_filtered.json()
        self.assertTrue(all(r["issue_type"] == "Waterlogging" for r in water_reports))

        # 3. Retrieve single issue details
        sample_id = reports[0]["id"]
        res_detail = self.client.get(f"/api/v1/issues/{sample_id}", headers=self.citizen_headers)
        self.assertEqual(res_detail.status_code, 200)
        detail = res_detail.json()
        self.assertEqual(detail["id"], sample_id)
        self.assertIn("department", detail)
        self.assertIn("status_history", detail)

    def test_12_municipal_status_updates_and_category_correction(self):
        """Exercise municipal issue status transition and category correction with validation."""
        # Create an issue
        payload = {
            "title": "Drainage Issue near Central Bus Stand",
            "description": "Reported drain condition",
            "issue_type": "Blocked Drains",
            "latitude": 13.0830,
            "longitude": 80.2710,
            "address": "Central Bus Stand",
            "original_image_url": "/uploads/original/drain_sample.jpg",
            "ai_confidence": 0.0,
            "severity": "HIGH",
            "priority_score": 75.0,
            "bounding_box_json": "[]",
            "ai_analysis_status": "MANUAL_OR_UNAVAILABLE"
        }
        res_create = self.client.post("/api/v1/issues", json=payload, headers=self.citizen_headers)
        issue_id = res_create.json()["id"]

        # Advance status: UNDER_REVIEW -> ASSIGNED -> IN_PROGRESS
        status_steps = ["UNDER_REVIEW", "ASSIGNED", "IN_PROGRESS"]
        for st in status_steps:
            res_st = self.client.patch(
                f"/api/v1/issues/{issue_id}/status",
                json={"status": st, "notes": f"Progressed to {st}"},
                headers=self.admin_headers
            )
            self.assertEqual(res_st.status_code, 200)
            self.assertEqual(res_st.json()["status"], st)

        # Category correction to another valid active category
        res_corr = self.client.patch(
            f"/api/v1/issues/{issue_id}/verify-category",
            json={"verified_category": "Overflowing Drains", "notes": "Inspector found drain overflowing onto pavement."},
            headers=self.admin_headers
        )
        self.assertEqual(res_corr.status_code, 200)
        self.assertEqual(res_corr.json()["verified_category"], "Overflowing Drains")

        # Invalid category rejection
        res_invalid = self.client.patch(
            f"/api/v1/issues/{issue_id}/verify-category",
            json={"verified_category": "Alien Spacecraft Crash", "notes": "Invalid"},
            headers=self.admin_headers
        )
        self.assertEqual(res_invalid.status_code, 400)

    def test_13_public_map_and_analytics_integrity(self):
        """Verify public map and analytics dashboard correctly aggregate persisted records."""
        res_map = self.client.get("/api/v1/issues/map-data")
        self.assertEqual(res_map.status_code, 200)
        points = res_map.json()
        self.assertIsInstance(points, list)
        self.assertGreater(len(points), 0)
        for pt in points:
            self.assertIn("latitude", pt)
            self.assertIn("longitude", pt)
            self.assertIn("issue_type", pt)
            self.assertIn("status", pt)

        res_analytics = self.client.get("/api/v1/analytics/dashboard")
        self.assertEqual(res_analytics.status_code, 200)
        analytics = res_analytics.json()
        self.assertGreater(analytics["total_issues"], 0)
        self.assertIn("issues_by_category", analytics)
        self.assertIn("issues_by_severity", analytics)
        self.assertIn("department_performance", analytics)

    def test_14_whole_image_classification_truthfulness_no_synthetic_boxes(self):
        """Verify IMAGE_CLASSIFICATION_ONLY reports without synthetic bounding boxes."""
        payload = {
            "title": "Severe Waterlogging along Subway Underpass",
            "description": "Entire road underpass submerged under water.",
            "issue_type": "Waterlogging",
            "latitude": 13.0840,
            "longitude": 80.2720,
            "address": "Subway Underpass",
            "original_image_url": "/uploads/original/waterlog_scene.jpg",
            "ai_confidence": 0.85,
            "severity": "HIGH",
            "priority_score": 80.0,
            "bounding_box_json": "[]", # Genuine empty bounding boxes for whole-image classification
            "ai_analysis_status": "SUCCESS"
        }
        res = self.client.post("/api/v1/issues", json=payload, headers=self.citizen_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "AI_ANALYZED")
        self.assertEqual(data["issue_type"], "Waterlogging")
        self.assertEqual(data["department"]["code"], "DEPT_DRAIN")
        # Ensure images table contains no synthetic bounding box
        self.assertEqual(data["images"][0]["bounding_box_json"], "[]")

    def test_15_failure_handling_and_no_orphaned_records(self):
        """Verify image upload errors fail cleanly without creating orphaned issue records."""
        # Record issue count before
        session = self.SessionLocal()
        count_before = session.query(Issue).count()
        session.close()

        # 1. Post invalid file extension
        bad_file = io.BytesIO(b"executable data")
        bad_file.name = "payload.exe"
        res_bad = self.client.post(
            "/api/v1/issues/analyze-image",
            files={"file": ("payload.exe", bad_file, "application/octet-stream")},
            headers=self.citizen_headers
        )
        self.assertEqual(res_bad.status_code, 400)
        self.assertIn("Invalid image format", res_bad.text)

        # 2. Record issue count after
        session = self.SessionLocal()
        count_after = session.query(Issue).count()
        session.close()
        self.assertEqual(count_before, count_after, "No orphaned issues should be created on upload failure!")

    def test_16_classifier_unavailable_truthful_reporting(self):
        """Verify truthful reporting when classification models are intended but weights are missing."""
        from app.services.models.registry import model_registry

        # 1. Verify adapter load status in runtime environment
        irdid_adapter = model_registry.get_adapter("irdid-classifier-candidate")
        self.assertIsNotNone(irdid_adapter, "IRDIDClassificationAdapter should be registered in model_registry")
        self.assertFalse(irdid_adapter.is_available, "IRDID weights must NOT be claimed as available without real weights file")

        # 2. Verify infer() returns truthful unsupported status
        test_img = os.path.join(self.temp_dir, "test_dummy.jpg")
        Image.new("RGB", (100, 100), color="blue").save(test_img)
        res_infer = irdid_adapter.infer(test_img)
        self.assertEqual(res_infer["status"], "unsupported")
        self.assertEqual(len(res_infer["raw_detections"]), 0)
        self.assertIn("not found", res_infer["error_message"])

        # 3. Verify /categories endpoint reports CLASSIFICATION_UNAVAILABLE and model_loaded: False
        res_cat = self.client.get("/api/v1/issues/categories")
        self.assertEqual(res_cat.status_code, 200)
        cats = {c["name"]: c for c in res_cat.json()["active_categories"]}
        self.assertIn("Damaged Road Surface", cats)
        self.assertIn("Waterlogging", cats)

        drs = cats["Damaged Road Surface"]
        self.assertEqual(drs["capability_category"], "CLASSIFICATION_UNAVAILABLE")
        self.assertFalse(drs["model_loaded"])

        wl = cats["Waterlogging"]
        self.assertEqual(wl["capability_category"], "CLASSIFICATION_UNAVAILABLE")
        self.assertFalse(wl["model_loaded"])

        # 4. Verify manual citizen reporting succeeds when model is unavailable
        payload_manual = {
            "title": "Manual report: Weathered shoulder along bypass",
            "description": "Observed crumbling asphalt edge",
            "issue_type": "Damaged Road Surface",
            "latitude": 13.0850,
            "longitude": 80.2730,
            "address": "Bypass Road Km 12",
            "original_image_url": "/uploads/original/shoulder.jpg",
            "ai_confidence": 0.0,
            "severity": "MEDIUM",
            "priority_score": 50.0,
            "bounding_box_json": "[]",
            "ai_analysis_status": "MANUAL_OR_UNAVAILABLE"
        }
        res_rep = self.client.post("/api/v1/issues", json=payload_manual, headers=self.citizen_headers)
        self.assertEqual(res_rep.status_code, 200)
        rep_data = res_rep.json()
        self.assertEqual(rep_data["status"], "REPORTED")
        self.assertEqual(rep_data["issue_type"], "Damaged Road Surface")
        self.assertEqual(rep_data["department"]["code"], "DEPT_PWD")
        self.assertEqual(rep_data["ai_analysis_status"], "MANUAL_OR_UNAVAILABLE")

    def test_17_classifier_available_mock_contract_verification(self):
        """
        Verify the architectural contract and schema handling when a classification model IS available.
        NOTE: This test uses a controlled mock adapter solely to verify pipeline schema and interface
        correctness (zero synthetic boxes, truthful provenance, department routing). It does NOT claim
        real-world model accuracy.
        """
        from typing import List, Dict, Any
        from app.services.models.registry import model_registry
        from app.services.models.base_adapter import BaseDefectModelAdapter

        class ControlledMockClassifier(BaseDefectModelAdapter):
            @property
            def model_id(self) -> str:
                return "mock-irdid-classifier-v1"

            @property
            def supported_categories(self) -> List[str]:
                return ["Damaged Road Surface", "Waterlogging"]

            @property
            def is_available(self) -> bool:
                return True

            def infer(self, image_path: str) -> Dict[str, Any]:
                return {
                    "status": "success",
                    "model_id": self.model_id,
                    "raw_detections": [
                        {
                            "class": "Damaged Road Surface",
                            "raw_class": "broken_edges",
                            "confidence": 0.88,
                            "bounding_box": None  # Genuine classification without bounding box
                        }
                    ],
                    "execution_time_ms": 15.0,
                    "error_message": None
                }

        mock_adapter = ControlledMockClassifier()
        orig_adapters = dict(model_registry._adapters)
        try:
            # Register mock adapter
            model_registry._adapters[mock_adapter.model_id] = mock_adapter

            # Run analyze_issue_image on a temporary test image
            test_img = os.path.join(self.temp_dir, "test_classified_scene.jpg")
            Image.new("RGB", (640, 480), color="gray").save(test_img)

            result = analyze_issue_image(test_img)
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["issue_type"], "Damaged Road Surface")
            self.assertAlmostEqual(result["confidence"], 0.88, places=2)
            # Crucial truthfulness check: Bounding boxes list MUST be empty for classification!
            self.assertEqual(result["bounding_boxes"], [], "Classification must NOT produce synthetic bounding boxes!")
            self.assertEqual(result["count"], 0)
            self.assertEqual(result["defect_area_ratio"], 0.0)
            self.assertFalse(result["is_real_yolo"], "Classification must not be attributed to YOLO")
            # Detected defects must record bounding_box as None
            self.assertIsNone(result["detected_defects"][0]["bounding_box"])

            # Verify report creation with this result persists truthfully
            payload = {
                "title": "Damaged Road Surface Verified Scene",
                "description": "Scene classification test",
                "issue_type": "Damaged Road Surface",
                "latitude": 13.0860,
                "longitude": 80.2740,
                "address": "Test Highway",
                "original_image_url": "/uploads/original/test_classified_scene.jpg",
                "ai_confidence": result["confidence"],
                "severity": result["severity"],
                "priority_score": result["priority_score"],
                "bounding_box_json": json.dumps(result["bounding_boxes"]),
                "detected_defects_json": json.dumps(result["detected_defects"]),
                "model_provenance_json": json.dumps(result["model_provenance"]),
                "ai_analysis_status": "SUCCESS"
            }
            res_post = self.client.post("/api/v1/issues", json=payload, headers=self.citizen_headers)
            self.assertEqual(res_post.status_code, 200)
            issue_data = res_post.json()
            self.assertEqual(issue_data["status"], "AI_ANALYZED")
            self.assertEqual(issue_data["issue_type"], "Damaged Road Surface")
            self.assertEqual(issue_data["department"]["code"], "DEPT_PWD")
            self.assertEqual(issue_data["images"][0]["bounding_box_json"], "[]")
        finally:
            # Restore model registry to pristine state
            model_registry._adapters = orig_adapters

    def test_18_yolo_first_spatial_arbitration_dual_model_coexistence(self):
        """
        Verify Phase 2 YOLO-first detection arbitration:
        When both a localized YOLO detection (Pothole at 0.65) and a whole-image
        classification (Damaged Road Surface at 0.92) are valid for the same image:
        1. Localized YOLO detection takes precedence as primary issue type.
        2. YOLO detection confidence (0.65) is selected over classifier (0.92).
        3. Localized bounding boxes are fully preserved.
        4. is_real_yolo is True.
        5. Classification is recorded as secondary scene context with bounding_box: None.
        6. Issue creation persists the primary YOLO defect and bounding boxes.
        """
        from typing import List, Dict, Any
        from app.services.models.registry import model_registry
        from app.services.models.base_adapter import BaseDefectModelAdapter

        class MockYOLODetector(BaseDefectModelAdapter):
            @property
            def model_id(self) -> str:
                return "yolov8-rdd2020-india-v1"

            @property
            def supported_categories(self) -> List[str]:
                return ["Pothole", "Longitudinal Crack", "Transverse Crack", "Alligator Crack"]

            @property
            def is_available(self) -> bool:
                return True

            def infer(self, image_path: str) -> Dict[str, Any]:
                return {
                    "status": "success",
                    "model_id": self.model_id,
                    "raw_detections": [
                        {
                            "class": "Pothole",
                            "raw_class": "D40",
                            "confidence": 0.65,
                            "bounding_box": [30, 40, 150, 160]
                        }
                    ],
                    "execution_time_ms": 14.0,
                    "error_message": None
                }

        class MockSceneClassifier(BaseDefectModelAdapter):
            @property
            def model_id(self) -> str:
                return "irdid-classifier-candidate"

            @property
            def supported_categories(self) -> List[str]:
                return ["Damaged Road Surface", "Waterlogging"]

            @property
            def is_available(self) -> bool:
                return True

            def infer(self, image_path: str) -> Dict[str, Any]:
                return {
                    "status": "success",
                    "model_id": self.model_id,
                    "raw_detections": [
                        {
                            "class": "Damaged Road Surface",
                            "raw_class": "broken_edges",
                            "confidence": 0.92,
                            "bounding_box": None
                        }
                    ],
                    "execution_time_ms": 10.0,
                    "error_message": None
                }

        mock_yolo = MockYOLODetector()
        mock_cls = MockSceneClassifier()
        orig_adapters = dict(model_registry._adapters)

        try:
            model_registry._adapters = {
                mock_yolo.model_id: mock_yolo,
                mock_cls.model_id: mock_cls
            }

            test_img = os.path.join(self.temp_dir, "test_dual_model_arbitration.jpg")
            Image.new("RGB", (640, 480), color="gray").save(test_img)

            result = analyze_issue_image(test_img)
            self.assertEqual(result["status"], "success")

            # Core arbitration check: YOLO Pothole (0.65) MUST win over Classifier Damaged Road Surface (0.92)
            self.assertEqual(result["issue_type"], "Pothole")
            self.assertAlmostEqual(result["confidence"], 0.65, places=2)
            self.assertTrue(result["is_real_yolo"])
            self.assertEqual(result["recommended_department_code"], "DEPT_PWD")

            # Spatial details: exactly 1 localized bounding box
            self.assertEqual(len(result["bounding_boxes"]), 1)
            self.assertEqual(result["count"], 1)
            self.assertEqual(result["bounding_boxes"][0]["class"], "Pothole")
            self.assertGreater(result["defect_area_ratio"], 0.0)

            # Secondary context: both defects recorded in detected_defects
            categories = [d["category"] for d in result["detected_defects"]]
            self.assertIn("Pothole", categories)
            self.assertIn("Damaged Road Surface", categories)
            pothole_entry = next(d for d in result["detected_defects"] if d["category"] == "Pothole")
            self.assertEqual(pothole_entry["bounding_box"], [30, 40, 120, 120])
            cls_entry = next(d for d in result["detected_defects"] if d["category"] == "Damaged Road Surface")
            self.assertIsNone(cls_entry["bounding_box"])

            # Verify issue submission persistence
            payload = {
                "title": "Dual-Model Arbitration Verified Pothole",
                "description": "Arbitration test report",
                "issue_type": result["issue_type"],
                "latitude": 13.0870,
                "longitude": 80.2750,
                "address": "Arbitration Boulevard",
                "original_image_url": "/uploads/original/test_dual_model_arbitration.jpg",
                "ai_confidence": result["confidence"],
                "severity": result["severity"],
                "priority_score": result["priority_score"],
                "bounding_box_json": json.dumps(result["bounding_boxes"]),
                "detected_defects_json": json.dumps(result["detected_defects"]),
                "model_provenance_json": json.dumps(result["model_provenance"]),
                "ai_analysis_status": "SUCCESS"
            }
            res_post = self.client.post("/api/v1/issues", json=payload, headers=self.citizen_headers)
            self.assertEqual(res_post.status_code, 200)
            data = res_post.json()
            self.assertEqual(data["status"], "AI_ANALYZED")
            self.assertEqual(data["issue_type"], "Pothole")
            self.assertEqual(data["department"]["code"], "DEPT_PWD")
            # Bounding boxes preserved in image record
            self.assertNotEqual(data["images"][0]["bounding_box_json"], "[]")
        finally:
            model_registry._adapters = orig_adapters

if __name__ == "__main__":
    unittest.main()
