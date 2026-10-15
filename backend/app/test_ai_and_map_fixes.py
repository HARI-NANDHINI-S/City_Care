import os
import unittest
import tempfile
import json
from PIL import Image
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.issue import Issue, IssueType, IssueStatus, SeverityLevel
from app.models.image import IssueImage
from app.core.security import get_password_hash, create_access_token
from app.services.ai_service import analyze_issue_image
from app.services.routing_service import get_recommended_department_code, get_recommended_department_name
from app.services.models.registry import model_registry
from app.core.defect_registry import DEFECT_REGISTRY, get_active_categories

class TestAIAndMapFixes(unittest.TestCase):
    """
    Automated regression suite verifying:
    1. Truthful YOLOv8 defect detection without false pothole fallbacks.
    2. Proper handling of normal road images (explicit no_detection).
    3. Multi-category manual reporting across all 15 categories with correct department routing.
    4. Map-data coordinate validation and serialization.
    """

    @classmethod
    def setUpClass(cls):
        # Create an isolated temporary SQLite database
        cls.temp_db_fd, cls.temp_db_path = tempfile.mkstemp(suffix=".db")
        cls.engine = create_engine(
            f"sqlite:///{cls.temp_db_path}",
            connect_args={"check_same_thread": False}
        )
        cls.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

        def override_get_db():
            db = cls.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

        # Seed test departments and users in isolated DB
        db = cls.TestingSessionLocal()
        cls.pwd_dept = Department(name="Road & Public Works Department", code="DEPT_PWD")
        cls.san_dept = Department(name="Waste Management & Sanitation Dept", code="DEPT_SAN")
        cls.drain_dept = Department(name="Stormwater Drainage Dept", code="DEPT_DRAIN")
        cls.elec_dept = Department(name="Electrical Infrastructure Dept", code="DEPT_ELEC")
        cls.sew_dept = Department(name="Sewerage & Sanitation Board", code="DEPT_SEW")
        db.add_all([cls.pwd_dept, cls.san_dept, cls.drain_dept, cls.elec_dept, cls.sew_dept])
        db.commit()

        cls.citizen = User(
            email="citizen_test@civicvision.ai",
            hashed_password=get_password_hash("TestPass123"),
            full_name="Citizen Tester",
            role=UserRole.CITIZEN
        )
        cls.officer = User(
            email="pwd_officer_test@civicvision.ai",
            hashed_password=get_password_hash("TestPass123"),
            full_name="PWD Officer Tester",
            role=UserRole.OFFICER,
            department_id=cls.pwd_dept.id
        )
        db.add_all([cls.citizen, cls.officer])
        db.commit()
        cls.pwd_dept_id = cls.pwd_dept.id
        cls.citizen_id = cls.citizen.id
        cls.citizen_token = create_access_token(subject=cls.citizen_id, role=cls.citizen.role.value)
        cls.citizen_headers = {"Authorization": f"Bearer {cls.citizen_token}"}
        db.close()

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        os.close(cls.temp_db_fd)
        if os.path.exists(cls.temp_db_path):
            try:
                os.remove(cls.temp_db_path)
            except OSError:
                pass

    def test_01_model_loading_and_class_consistency(self):
        """Verify YOLO adapter loads best.pt and maps exactly 4 RDD2020 classes."""
        adapter = model_registry.get_adapter("yolov8-rdd2020-india-v1")
        self.assertIsNotNone(adapter)
        self.assertTrue(adapter.is_available)
        self.assertEqual(
            sorted(adapter.supported_categories),
            sorted(["Pothole", "Longitudinal Crack", "Transverse Crack", "Alligator Crack"])
        )
        # Verify 4 RDD classes mapping
        self.assertEqual(adapter.CLASS_MAPPING["D00"], "Longitudinal Crack")
        self.assertEqual(adapter.CLASS_MAPPING["D10"], "Transverse Crack")
        self.assertEqual(adapter.CLASS_MAPPING["D20"], "Alligator Crack")
        self.assertEqual(adapter.CLASS_MAPPING["D40"], "Pothole")

    def test_02_normal_road_image_no_fabricated_pothole(self):
        """Ensure a plain normal road image produces status='no_detection' and NEVER fabricates a pothole."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            plain_img = Image.new("RGB", (640, 640), color=(75, 75, 75))
            plain_img.save(f.name)
            temp_path = f.name

        try:
            result = analyze_issue_image(temp_path)
            self.assertEqual(result["status"], "no_detection")
            self.assertIsNone(result["issue_type"])
            self.assertIsNone(result["confidence"])
            self.assertEqual(result["bounding_boxes"], [])
            self.assertIn("No infrastructure defect detected", result["message"])
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_03_invalid_corrupted_image_handling(self):
        """Ensure invalid or truncated files report analysis_failed gracefully."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"NOT_A_VALID_IMAGE_DATA_CORRUPT")
            temp_path = f.name

        try:
            result = analyze_issue_image(temp_path)
            self.assertEqual(result["status"], "analysis_failed")
            self.assertIn("Corrupt or invalid image", result["message"])
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_04_supported_road_defect_pothole_detection(self):
        """Verify real pothole detection on Indian dataset test image if present."""
        test_img = "Indian-Road-Damage-Infrastructure-Dataset/images/potholes/img0001.jpg"
        if os.path.exists(test_img):
            result = analyze_issue_image(test_img)
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["issue_type"], "Pothole")
            self.assertGreater(result["confidence"], 0.25)
            self.assertGreater(len(result["bounding_boxes"]), 0)
            self.assertEqual(result["recommended_department_code"], "DEPT_PWD")

    def test_05_supported_road_defect_crack_detection(self):
        """Verify real crack detection on Indian dataset test image if present."""
        test_img = "Indian-Road-Damage-Infrastructure-Dataset/images/cracks/img0204.jpg"
        if os.path.exists(test_img):
            result = analyze_issue_image(test_img)
            self.assertEqual(result["status"], "success")
            self.assertIn(result["issue_type"], ["Longitudinal Crack", "Alligator Crack", "Transverse Crack"])
            self.assertGreater(result["confidence"], 0.25)

    def test_06_department_routing_for_all_15_categories(self):
        """Verify that every one of the 15 categories has an explicit, valid department routing."""
        all_15 = list(DEFECT_REGISTRY.keys())
        self.assertEqual(len(all_15), 15)

        for cat in all_15:
            dept_code = get_recommended_department_code(cat)
            dept_name = get_recommended_department_name(cat)
            self.assertIn(dept_code, ["DEPT_PWD", "DEPT_SAN", "DEPT_DRAIN", "DEPT_ELEC", "DEPT_SEW"])
            self.assertTrue(len(dept_name) > 0)

        # Explicit department assignments
        self.assertEqual(get_recommended_department_code("Pothole"), "DEPT_PWD")
        self.assertEqual(get_recommended_department_code("Damaged Road Surface"), "DEPT_PWD")
        self.assertEqual(get_recommended_department_code("Road Damage"), "DEPT_PWD")
        self.assertEqual(get_recommended_department_code("Garbage Accumulation"), "DEPT_SAN")
        self.assertEqual(get_recommended_department_code("Illegal Dumping"), "DEPT_SAN")
        self.assertEqual(get_recommended_department_code("Overflowing Garbage Bins"), "DEPT_SAN")
        self.assertEqual(get_recommended_department_code("Blocked Drains"), "DEPT_DRAIN")
        self.assertEqual(get_recommended_department_code("Overflowing Drains"), "DEPT_DRAIN")
        self.assertEqual(get_recommended_department_code("Waterlogging"), "DEPT_DRAIN")
        self.assertEqual(get_recommended_department_code("Damaged Drainage Covers"), "DEPT_DRAIN")
        self.assertEqual(get_recommended_department_code("Open Manhole"), "DEPT_SEW")
        self.assertEqual(get_recommended_department_code("Broken Streetlight"), "DEPT_ELEC")

    def test_07_manual_reporting_for_non_yolo_categories(self):
        """Verify citizen can report non-YOLO categories (Sanitation, Utilities) and receive proper routing."""
        # 1. Report Garbage Accumulation
        res_san = self.client.post(
            "/api/v1/issues",
            json={
                "title": "Overflowing waste near park",
                "description": "Garbage has spilled across the sidewalk",
                "issue_type": "Garbage Accumulation",
                "latitude": 28.6200,
                "longitude": 77.2100,
                "address": "Park Street Gate 2",
                "original_image_url": "/uploads/original/test_garbage.jpg",
                "ai_confidence": 0,
                "severity": "HIGH",
                "priority_score": 55.0,
                "ai_analysis_status": "MANUAL"
            },
            headers=self.citizen_headers
        )
        self.assertEqual(res_san.status_code, 200)
        data_san = res_san.json()
        self.assertEqual(data_san["issue_type"], "Garbage Accumulation")
        self.assertEqual(data_san["status"], "REPORTED")
        self.assertFalse(data_san["is_verified"])
        self.assertEqual(data_san["department"]["code"], "DEPT_SAN")

        # 2. Report Open Manhole (Utility category)
        res_util = self.client.post(
            "/api/v1/issues",
            json={
                "title": "Open manhole hazard",
                "description": "Cover missing on main street",
                "issue_type": "Open Manhole",
                "latitude": 28.6250,
                "longitude": 77.2150,
                "address": "Market Road",
                "original_image_url": "/uploads/original/test_manhole.jpg",
                "ai_confidence": 0,
                "severity": "CRITICAL",
                "priority_score": 90.0,
                "ai_analysis_status": "MANUAL"
            },
            headers=self.citizen_headers
        )
        self.assertEqual(res_util.status_code, 200)
        data_util = res_util.json()
        self.assertEqual(data_util["issue_type"], "Open Manhole")
        self.assertEqual(data_util["department"]["code"], "DEPT_SEW")

        # 3. Report Broken Streetlight (Utility category)
        res_light = self.client.post(
            "/api/v1/issues",
            json={
                "title": "Dark street luminaire",
                "description": "Pole 14 light not working",
                "issue_type": "Broken Streetlight",
                "latitude": 28.6300,
                "longitude": 77.2200,
                "address": "North Avenue",
                "original_image_url": "/uploads/original/test_light.jpg",
                "ai_confidence": 0,
                "severity": "MEDIUM",
                "priority_score": 45.0,
                "ai_analysis_status": "MANUAL"
            },
            headers=self.citizen_headers
        )
        self.assertEqual(res_light.status_code, 200)
        data_light = res_light.json()
        self.assertEqual(data_light["issue_type"], "Broken Streetlight")
        self.assertEqual(data_light["department"]["code"], "DEPT_ELEC")

    def test_08_disagreement_citizen_override_preserved(self):
        """Ensure that when a citizen keeps their category despite AI detection, citizen category is preserved."""
        res_disagree = self.client.post(
            "/api/v1/issues",
            json={
                "title": "Weathered Road Shoulder",
                "description": "Severe edge breakdown",
                "issue_type": "Damaged Road Surface",  # Citizen choice
                "latitude": 28.6150,
                "longitude": 77.2050,
                "address": "Ring Road KM 12",
                "original_image_url": "/uploads/original/edge.jpg",
                "ai_confidence": 0,  # Zeroed out because citizen overrode AI
                "severity": "HIGH",
                "priority_score": 65.0,
                "detected_defects_json": json.dumps([{"category": "Pothole", "confidence": 0.32}]),
                "ai_analysis_status": "CITIZEN_OVERRODE_AI"
            },
            headers=self.citizen_headers
        )
        self.assertEqual(res_disagree.status_code, 200)
        data = res_disagree.json()
        self.assertEqual(data["issue_type"], "Damaged Road Surface")
        self.assertEqual(data["status"], "REPORTED")
        self.assertEqual(data["ai_analysis_status"], "CITIZEN_OVERRODE_AI")
        self.assertFalse(data["is_verified"])

    def test_09_map_data_endpoint_validation_and_sanitization(self):
        """Verify /api/v1/issues/map-data sanitizes coordinates and returns valid numeric points."""
        res = self.client.get("/api/v1/issues/map-data")
        self.assertEqual(res.status_code, 200)
        points = res.json()
        self.assertIsInstance(points, list)
        self.assertGreater(len(points), 0)

        for pt in points:
            self.assertIn("id", pt)
            self.assertIn("title", pt)
            self.assertIn("issue_type", pt)
            self.assertIn("latitude", pt)
            self.assertIn("longitude", pt)
            self.assertIn("status", pt)
            self.assertIn("priority_score", pt)

            # Strict numeric bounds
            self.assertIsInstance(pt["latitude"], float)
            self.assertIsInstance(pt["longitude"], float)
            self.assertTrue(-90.0 <= pt["latitude"] <= 90.0)
            self.assertTrue(-180.0 <= pt["longitude"] <= 180.0)

    def test_10_map_data_skips_invalid_coordinates(self):
        """Verify that an issue with out-of-range coordinates is safely excluded from map-data."""
        db = self.TestingSessionLocal()
        invalid_issue = Issue(
            title="Invalid Coords Issue",
            description="Testing coords safety",
            issue_type=IssueType.POTHOLE,
            latitude=999.0,  # Invalid latitude
            longitude=77.0,
            reporter_id=self.citizen_id,
            department_id=self.pwd_dept_id,
            status=IssueStatus.REPORTED,
            severity=SeverityLevel.LOW,
            priority_score=10.0
        )
        db.add(invalid_issue)
        db.commit()
        invalid_id = invalid_issue.id
        db.close()

        res = self.client.get("/api/v1/issues/map-data")
        self.assertEqual(res.status_code, 200)
        points = res.json()
        returned_ids = [p["id"] for p in points]
        self.assertNotIn(invalid_id, returned_ids)

if __name__ == "__main__":
    unittest.main()
