"""
CivicVision AI — Phase 4: Human Verification and Safe Triage Regression Test Suite
===================================================================================

Comprehensive, isolated regression tests covering all 10 mandated scenarios for
human verification and safe triage:
1. AI suggestions remain unverified until a human decision is recorded.
2. Authorized reviewers can perform permitted review actions (confirm, correct, reject suggestion, request info).
3. Unauthorized users (citizens, officers of another dept, unauthenticated) cannot triage reports.
4. Review decisions, reviewer identity, and timestamps persist correctly in audit history.
5. Rejected predictions do not erase the original complaint or evidence.
6. Manual reports continue to work independently of AI.
7. Image-level classifications do not produce fabricated bounding boxes or measured defect areas.
8. Existing YOLO-first arbitration and confidence filtering remain intact.
9. Existing feature-flag behavior remains intact (ENABLE_IRDID_CLASSIFIER=False).
10. Database tests use temporary, isolated SQLite databases and do not modify real user data.
"""

import os
import sys
import json
import tempfile
import shutil
import unittest
from pathlib import Path
from PIL import Image

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.issue import Issue, IssueStatus, IssueType, SeverityLevel
from app.models.history import IssueStatusHistory
from app.schemas.issue import IssueDetailOut
from app.core.security import get_password_hash
from app.core.defect_registry import DEFECT_REGISTRY, ACTIVE_12_CATEGORIES
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
            "execution_time_ms": 10.0,
            "error_message": None
        }


class MockClassificationAdapter(BaseDefectModelAdapter):
    def __init__(self, detections=None, available=True):
        self._detections = detections or []
        self._available = available

    @property
    def model_id(self) -> str:
        return "irdid-classifier-candidate"

    @property
    def supported_categories(self):
        return ["Damaged Road Surface", "Waterlogging"]

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
            "execution_time_ms": 5.0,
            "error_message": None
        }


class TestHumanVerificationAndSafeTriage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Setup isolated ephemeral directory and SQLite database
        cls.temp_dir = tempfile.mkdtemp(prefix="civicvision_human_verification_test_")
        cls.test_db_path = os.path.join(cls.temp_dir, "human_verification_test.db")
        cls.test_db_url = f"sqlite:///{cls.test_db_path}"

        # Safety check: ensure production databases are never touched
        assert "civicsense.db" not in cls.test_db_url.lower()
        assert "civicvision.db" not in cls.test_db_url.lower()

        cls.engine = create_engine(cls.test_db_url, connect_args={"check_same_thread": False})
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

        session = cls.SessionLocal()
        # Seed departments
        cls.dept_pwd = Department(name="Road & Public Works Department", code="DEPT_PWD", description="Roads")
        cls.dept_san = Department(name="Waste Management & Sanitation Dept", code="DEPT_SAN", description="Sanitation")
        cls.dept_drain = Department(name="Stormwater Drainage Dept", code="DEPT_DRAIN", description="Drainage")
        session.add_all([cls.dept_pwd, cls.dept_san, cls.dept_drain])
        session.commit()

        # Seed users: 1 Citizen, 1 Admin, 1 PWD Officer, 1 Sanitation Officer
        cls.citizen = User(
            full_name="Citizen Tester",
            email="citizen.hv@civicvision.ai",
            hashed_password=get_password_hash("TestPass@123"),
            role=UserRole.CITIZEN
        )
        cls.admin = User(
            full_name="Municipal Administrator",
            email="admin.hv@civicvision.ai",
            hashed_password=get_password_hash("TestPass@123"),
            role=UserRole.ADMIN
        )
        cls.officer_pwd = User(
            full_name="PWD Inspector",
            email="officer.pwd@civicvision.ai",
            hashed_password=get_password_hash("TestPass@123"),
            role=UserRole.OFFICER,
            department_id=cls.dept_pwd.id
        )
        cls.officer_san = User(
            full_name="Sanitation Inspector",
            email="officer.san@civicvision.ai",
            hashed_password=get_password_hash("TestPass@123"),
            role=UserRole.OFFICER,
            department_id=cls.dept_san.id
        )
        session.add_all([cls.citizen, cls.admin, cls.officer_pwd, cls.officer_san])
        session.commit()

        cls.citizen_id = cls.citizen.id
        cls.admin_id = cls.admin.id
        cls.officer_pwd_id = cls.officer_pwd.id
        cls.officer_san_id = cls.officer_san.id

        session.close()


        def override_get_db():
            db = cls.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

        # Login tokens
        res_c = cls.client.post("/api/v1/auth/login", json={"email": "citizen.hv@civicvision.ai", "password": "TestPass@123"})
        cls.citizen_headers = {"Authorization": f"Bearer {res_c.json()['access_token']}"}

        res_a = cls.client.post("/api/v1/auth/login", json={"email": "admin.hv@civicvision.ai", "password": "TestPass@123"})
        cls.admin_headers = {"Authorization": f"Bearer {res_a.json()['access_token']}"}

        res_o = cls.client.post("/api/v1/auth/login", json={"email": "officer.pwd@civicvision.ai", "password": "TestPass@123"})
        cls.pwd_officer_headers = {"Authorization": f"Bearer {res_o.json()['access_token']}"}

        res_s = cls.client.post("/api/v1/auth/login", json={"email": "officer.san@civicvision.ai", "password": "TestPass@123"})
        cls.san_officer_headers = {"Authorization": f"Bearer {res_s.json()['access_token']}"}

        # Create dummy test image fixture
        cls.test_img_path = os.path.join(cls.temp_dir, "dummy_triage.jpg")
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
        model_registry._adapters = dict(self._orig_adapters)

    # -------------------------------------------------------------------------
    # Scenario 1: AI suggestions remain unverified until a human decision is recorded
    # -------------------------------------------------------------------------
    def test_01_ai_suggestions_remain_unverified_until_human_decision(self):
        payload = {
            "title": "Severe Pothole on Sector 9 Avenue",
            "description": "Vehicle damaged due to road crater.",
            "issue_type": "Pothole",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "address": "Sector 9 Avenue, Delhi",
            "original_image_url": "/uploads/original/pothole1.jpg",
            "annotated_image_url": "/uploads/annotated/ann_pothole1.jpg",
            "ai_confidence": 0.88,
            "severity": "HIGH",
            "priority_score": 78.5,
            "bounding_box_json": json.dumps([{"class": "Pothole", "x": 100, "y": 150, "width": 200, "height": 120}]),
            "detected_defects_json": json.dumps([{"category": "Pothole", "confidence": 0.88, "bounding_box": [100, 150, 200, 120]}]),
            "ai_analysis_status": "SUCCESS"
        }
        res = self.client.post("/api/v1/issues", json=payload, headers=self.citizen_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        # Check that the prediction is strictly an unverified suggestion
        self.assertEqual(data["status"], "AI_ANALYZED")
        self.assertIsNone(data["verified_category"])
        self.assertFalse(data["is_verified"])
        self.assertEqual(data["verification_status"], "UNVERIFIED")
        self.assertEqual(data["ai_suggested_category"], "Pothole")
        self.assertEqual(data["ai_confidence"], 0.88)

    # -------------------------------------------------------------------------
    # Scenario 2: Authorized reviewers can perform permitted review actions
    # -------------------------------------------------------------------------
    def test_02_authorized_reviewers_can_perform_triage_actions(self):
        # 2a. Confirm action by Municipal Admin
        payload = {
            "title": "Crack along Ring Road",
            "issue_type": "Longitudinal Crack",
            "latitude": 28.6140,
            "longitude": 77.2095,
            "original_image_url": "/uploads/original/crack.jpg",
            "ai_confidence": 0.82,
            "severity": "MEDIUM",
            "priority_score": 62.0,
            "bounding_box_json": "[]",
            "ai_analysis_status": "SUCCESS"
        }
        create_res = self.client.post("/api/v1/issues", json=payload, headers=self.citizen_headers)
        issue_id = create_res.json()["id"]

        triage_payload = {
            "decision": "CONFIRM",
            "notes": "Field inspection confirmed longitudinal crack matching AI suggestion."
        }
        res_confirm = self.client.post(f"/api/v1/issues/{issue_id}/triage", json=triage_payload, headers=self.admin_headers)
        self.assertEqual(res_confirm.status_code, 200)
        confirmed_data = res_confirm.json()

        self.assertTrue(confirmed_data["is_verified"])
        self.assertEqual(confirmed_data["verified_category"], "Longitudinal Crack")
        self.assertEqual(confirmed_data["verification_status"], "CONFIRMED")
        self.assertEqual(confirmed_data["status"], "UNDER_REVIEW")

        # 2b. Correct / Reclassify action by authorized Department Officer
        triage_correct = {
            "decision": "CORRECT",
            "verified_category": "Alligator Crack",
            "notes": "Inspector notes fatigue alligator cracking pattern rather than single longitudinal crack."
        }
        res_correct = self.client.post(f"/api/v1/issues/{issue_id}/triage", json=triage_correct, headers=self.pwd_officer_headers)
        self.assertEqual(res_correct.status_code, 200)
        corrected_data = res_correct.json()

        self.assertTrue(corrected_data["is_verified"])
        self.assertEqual(corrected_data["verified_category"], "Alligator Crack")
        self.assertEqual(corrected_data["verification_status"], "CORRECTED")
        # Ensure original citizen/AI category is preserved in issue_type
        self.assertEqual(corrected_data["issue_type"], "Longitudinal Crack")

        # 2c. Request Information action
        triage_info = {
            "decision": "REQUEST_INFO",
            "notes": "Please provide the nearest pillar or kilometer stone number for precise crew dispatch."
        }
        res_info = self.client.post(f"/api/v1/issues/{issue_id}/triage", json=triage_info, headers=self.pwd_officer_headers)
        self.assertEqual(res_info.status_code, 200)
        info_data = res_info.json()
        self.assertIn("nearest pillar", info_data["latest_update"])

    # -------------------------------------------------------------------------
    # Scenario 3: Unauthorized users cannot verify or reject reports
    # -------------------------------------------------------------------------
    def test_03_unauthorized_users_cannot_verify_or_reject_reports(self):
        payload = {
            "title": "Suspected Pothole for Auth Check",
            "issue_type": "Pothole",
            "latitude": 28.6145,
            "longitude": 77.2100,
            "original_image_url": "/uploads/original/auth_test.jpg",
            "ai_confidence": 0.75,
            "severity": "HIGH",
            "priority_score": 70.0,
            "ai_analysis_status": "SUCCESS"
        }
        create_res = self.client.post("/api/v1/issues", json=payload, headers=self.citizen_headers)
        issue_id = create_res.json()["id"]

        triage_body = {"decision": "CONFIRM", "notes": "Unauthorized attempt"}

        # 3a. Citizen cannot triage reports (403 Forbidden)
        res_cit = self.client.post(f"/api/v1/issues/{issue_id}/triage", json=triage_body, headers=self.citizen_headers)
        self.assertEqual(res_cit.status_code, 403)

        # 3b. Citizen cannot call /verify-category (403 Forbidden)
        res_cit_vc = self.client.patch(f"/api/v1/issues/{issue_id}/verify-category", json={"verified_category": "Pothole"}, headers=self.citizen_headers)
        self.assertEqual(res_cit_vc.status_code, 403)

        # 3c. Officer from an unrelated department cannot triage PWD issue (403 Forbidden)
        res_wrong_dept = self.client.post(f"/api/v1/issues/{issue_id}/triage", json=triage_body, headers=self.san_officer_headers)
        self.assertEqual(res_wrong_dept.status_code, 403)

        # 3d. Unauthenticated request without JWT token (401 Unauthorized)
        res_unauth = self.client.post(f"/api/v1/issues/{issue_id}/triage", json=triage_body)
        self.assertEqual(res_unauth.status_code, 401)

    # -------------------------------------------------------------------------
    # Scenario 4: Review decisions, reviewer identity, and timestamps persist correctly
    # -------------------------------------------------------------------------
    def test_04_review_decisions_and_timestamps_persist_in_audit_history(self):
        payload = {
            "title": "Audit Trail Verification Defect",
            "issue_type": "Transverse Crack",
            "latitude": 28.6150,
            "longitude": 77.2105,
            "original_image_url": "/uploads/original/audit.jpg",
            "ai_confidence": 0.79,
            "severity": "MEDIUM",
            "priority_score": 58.0,
            "ai_analysis_status": "SUCCESS"
        }
        create_res = self.client.post("/api/v1/issues", json=payload, headers=self.citizen_headers)
        issue_id = create_res.json()["id"]

        # Officer confirms
        triage_payload = {
            "decision": "CONFIRM",
            "notes": "Verified by PWD engineering team."
        }
        res = self.client.post(f"/api/v1/issues/{issue_id}/triage", json=triage_payload, headers=self.pwd_officer_headers)
        self.assertEqual(res.status_code, 200)

        # Inspect database audit log directly via independent session
        session = self.SessionLocal()
        issue_db = session.query(Issue).filter_by(id=issue_id).first()
        self.assertIsNotNone(issue_db)
        self.assertEqual(issue_db.verified_category, "Transverse Crack")

        # Find the audit history entry for triage confirmation
        history_entry = (
            session.query(IssueStatusHistory)
            .filter_by(issue_id=issue_id, new_status=IssueStatus.UNDER_REVIEW)
            .order_by(IssueStatusHistory.created_at.desc())
            .first()
        )
        self.assertIsNotNone(history_entry)
        self.assertEqual(history_entry.changed_by_user_id, self.officer_pwd_id)
        self.assertIn("CONFIRMED", history_entry.notes)
        self.assertIn("PWD Inspector", history_entry.notes)
        self.assertIsNotNone(history_entry.created_at)
        session.close()

    # -------------------------------------------------------------------------
    # Scenario 5: Rejected predictions do not erase the original complaint or evidence
    # -------------------------------------------------------------------------
    def test_05_rejected_predictions_do_not_erase_original_complaint_or_evidence(self):
        payload = {
            "title": "Water stain mistaken for Pothole",
            "description": "Citizen reports large dark mark on road.",
            "issue_type": "Pothole",
            "latitude": 28.6155,
            "longitude": 77.2110,
            "address": "Opposite City Hall, Lane 3",
            "original_image_url": "/uploads/original/stain.jpg",
            "annotated_image_url": "/uploads/annotated/ann_stain.jpg",
            "ai_confidence": 0.65,
            "severity": "HIGH",
            "priority_score": 68.0,
            "bounding_box_json": json.dumps([{"class": "Pothole", "x": 50, "y": 60, "width": 80, "height": 70}]),
            "detected_defects_json": json.dumps([{"category": "Pothole", "confidence": 0.65}]),
            "ai_analysis_status": "SUCCESS"
        }
        create_res = self.client.post("/api/v1/issues", json=payload, headers=self.citizen_headers)
        issue_id = create_res.json()["id"]

        # Reviewer rejects the AI suggestion as false positive
        reject_payload = {
            "decision": "REJECT_SUGGESTION",
            "notes": "High-contrast shadow of tree branches falsely identified as pothole. Surface asphalt is smooth."
        }
        res_reject = self.client.post(f"/api/v1/issues/{issue_id}/triage", json=reject_payload, headers=self.pwd_officer_headers)
        self.assertEqual(res_reject.status_code, 200)
        rejected_data = res_reject.json()

        # 1. Report is NOT deleted and NOT closed; remains accessible under review
        self.assertNotEqual(rejected_data["status"], "CLOSED")
        self.assertEqual(rejected_data["status"], "UNDER_REVIEW")

        # 2. Rejection state explicitly distinguished
        self.assertEqual(rejected_data["verified_category"], "REJECTED_AS_FALSE_POSITIVE")
        self.assertEqual(rejected_data["verification_status"], "REJECTED")
        self.assertFalse(rejected_data["is_verified"])
        self.assertEqual(rejected_data["ai_analysis_status"], "AI_SUGGESTION_REJECTED")

        # 3. Citizen's original complaint, description, GPS, and evidence are preserved
        self.assertEqual(rejected_data["title"], "Water stain mistaken for Pothole")
        self.assertEqual(rejected_data["description"], "Citizen reports large dark mark on road.")
        self.assertEqual(rejected_data["address"], "Opposite City Hall, Lane 3")
        self.assertEqual(rejected_data["latitude"], 28.6155)
        self.assertEqual(rejected_data["longitude"], 77.2110)
        self.assertEqual(len(rejected_data["images"]), 1)
        self.assertEqual(rejected_data["images"][0]["original_image_path"], "/uploads/original/stain.jpg")
        self.assertIn("50", rejected_data["images"][0]["bounding_box_json"])

        # 4. Original AI suggestion is preserved in issue_type and detected_defects_json
        self.assertEqual(rejected_data["issue_type"], "Pothole")
        self.assertIn("Pothole", rejected_data["detected_defects_json"])

    # -------------------------------------------------------------------------
    # Scenario 6: Manual reports continue to work independently of AI
    # -------------------------------------------------------------------------
    def test_06_manual_reports_work_independently_of_ai(self):
        manual_payload = {
            "title": "Overflowing bin near school gate",
            "description": "Trash container overflowing since Monday.",
            "issue_type": "Overflowing Garbage Bins",
            "latitude": 28.6160,
            "longitude": 77.2115,
            "address": "Near DAV School, Block C",
            "original_image_url": "/uploads/original/bin_overflow.jpg",
            "annotated_image_url": None,
            "ai_confidence": 0.0,
            "severity": "MEDIUM",
            "priority_score": 45.0,
            "bounding_box_json": "[]",
            "ai_analysis_status": "MANUAL_OR_UNAVAILABLE"
        }
        res = self.client.post("/api/v1/issues", json=manual_payload, headers=self.citizen_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        # Issue created in REPORTED status
        self.assertEqual(data["status"], "REPORTED")
        self.assertFalse(data["is_verified"])
        self.assertEqual(data["verification_status"], "UNVERIFIED")
        self.assertIsNone(data["verified_category"])

        # Sanitation officer verifies manual category
        verify_res = self.client.post(
            f"/api/v1/issues/{data['id']}/triage",
            json={"decision": "CONFIRM", "notes": "Sanitation supervisor verified overflowing bin on site."},
            headers=self.san_officer_headers
        )
        self.assertEqual(verify_res.status_code, 200)
        verified_data = verify_res.json()
        self.assertTrue(verified_data["is_verified"])
        self.assertEqual(verified_data["verified_category"], "Overflowing Garbage Bins")
        self.assertEqual(verified_data["status"], "UNDER_REVIEW")

    # -------------------------------------------------------------------------
    # Scenario 7: Image-level classifications do not produce fabricated bounding boxes
    # -------------------------------------------------------------------------
    def test_07_image_level_classifications_do_not_produce_fabricated_bounding_boxes(self):
        # Register mock classification adapter returning Damaged Road Surface (confidence 0.85)
        cls_mock = MockClassificationAdapter(
            detections=[{"class": "Damaged Road Surface", "confidence": 0.85}],
            available=True
        )
        model_registry._adapters[cls_mock.model_id] = cls_mock
        model_registry._adapters.pop("yolov8-rdd2020-india-v1", None)

        res = analyze_issue_image(self.test_img_path)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["issue_type"], "Damaged Road Surface")
        self.assertEqual(res["confidence"], 0.85)

        # Safety requirement: Image-level classifications must NEVER synthesize bounding boxes
        self.assertEqual(res["bounding_boxes"], [], "Classification category must not have localized bounding boxes")
        self.assertEqual(res["count"], 0)
        self.assertEqual(res["defect_area_ratio"], 0.0)

        for det in res["detected_defects"]:
            if det["category"] == "Damaged Road Surface":
                self.assertIsNone(det["bounding_box"], "Classification defect must have bounding_box: None")

    # -------------------------------------------------------------------------
    # Scenario 8: Existing YOLO-first arbitration and confidence filtering remain intact
    # -------------------------------------------------------------------------
    def test_08_existing_yolo_first_arbitration_and_confidence_filtering_intact(self):
        # Localized YOLO pothole (conf: 0.40) vs Classifier Damaged Road Surface (conf: 0.90)
        yolo_mock = MockYOLOAdapter(detections=[
            {"class": "Pothole", "confidence": 0.40, "bounding_box": [100, 100, 250, 250]}
        ])
        cls_mock = MockClassificationAdapter(
            detections=[{"class": "Damaged Road Surface", "confidence": 0.90}],
            available=True
        )
        model_registry._adapters[yolo_mock.model_id] = yolo_mock
        model_registry._adapters[cls_mock.model_id] = cls_mock

        res = analyze_issue_image(self.test_img_path)
        # YOLO-first spatial precedence: Pothole selected despite lower confidence
        self.assertEqual(res["issue_type"], "Pothole")
        self.assertEqual(res["confidence"], 0.40)
        self.assertEqual(len(res["bounding_boxes"]), 1)
        self.assertEqual(res["bounding_boxes"][0]["class"], "Pothole")

        # Confidence filtering: YOLO prediction below threshold (e.g. 0.20 < 0.25) must be discarded
        yolo_below = MockYOLOAdapter(detections=[
            {"class": "Pothole", "confidence": 0.20, "bounding_box": [100, 100, 250, 250]}
        ])
        model_registry._adapters[yolo_below.model_id] = yolo_below
        model_registry._adapters.pop("irdid-classifier-candidate", None)

        res_filtered = analyze_issue_image(self.test_img_path)
        self.assertEqual(res_filtered["status"], "no_detection")
        self.assertIsNone(res_filtered["issue_type"])

    # -------------------------------------------------------------------------
    # Scenario 9: Existing feature-flag behavior remains intact
    # -------------------------------------------------------------------------
    def test_09_existing_feature_flag_behavior_remains_intact(self):
        # 1. Feature flag is disabled by default
        self.assertFalse(settings.ENABLE_IRDID_CLASSIFIER)

        # 2. Production classification adapter is unavailable when flag is false
        adapter = IRDIDClassificationAdapter()
        self.assertFalse(adapter.is_enabled)
        self.assertFalse(adapter.is_available)

        # 3. Model registry does not activate the quarantined classifier
        active_adapters = model_registry.get_all_active_adapters()
        for a in active_adapters:
            self.assertNotEqual(a.model_id, "irdid-classifier-candidate")

    # -------------------------------------------------------------------------
    # Scenario 10: Database tests use temporary SQLite databases and do not modify real data
    # -------------------------------------------------------------------------
    def test_10_database_isolation_and_no_real_user_data_mutation(self):
        # Ensure our test engine points to a dedicated temp directory
        self.assertTrue(os.path.exists(self.test_db_path))
        self.assertIn("civicvision_human_verification_test_", self.test_db_path)

        # Verify real database paths are completely untouched by this test session
        real_db_candidates = [
            os.path.join(str(backend_dir), "app", "civicvision.db"),
            os.path.join(str(backend_dir), "app", "civicsense.db"),
            os.path.join(str(backend_dir), "civicvision.db"),
            os.path.join(str(backend_dir), "civicsense.db"),
        ]
        import sqlite3
        for db_file in real_db_candidates:
            if os.path.exists(db_file) and os.path.getsize(db_file) > 0:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                if cursor.fetchone():
                    cursor.execute("SELECT email FROM users WHERE lower(email) LIKE '%@civicvision.ai'")
                    emails = [row[0] for row in cursor.fetchall()]
                    self.assertNotIn("citizen.hv@civicvision.ai", emails)
                conn.close()

    # -------------------------------------------------------------------------
    # Scenario 11: Persistence across separate database sessions and simulated restart
    # -------------------------------------------------------------------------
    def test_11_persistence_across_separate_sessions_and_simulated_restart(self):
        payload = {
            "title": "Persistence Audit Pothole",
            "description": "Deep asphalt crater on Main Road.",
            "issue_type": "Pothole",
            "latitude": 28.6170,
            "longitude": 77.2120,
            "address": "Main Road, Sector 5",
            "original_image_url": "/uploads/original/pothole_persist.jpg",
            "ai_confidence": 0.89,
            "severity": "HIGH",
            "priority_score": 75.0,
            "bounding_box_json": json.dumps([{"class": "Pothole", "x": 10, "y": 20, "width": 100, "height": 80}]),
            "detected_defects_json": json.dumps([{"category": "Pothole", "confidence": 0.89, "bounding_box": [10, 20, 100, 80]}]),
            "ai_analysis_status": "SUCCESS"
        }
        res = self.client.post("/api/v1/issues", json=payload, headers=self.citizen_headers)
        self.assertEqual(res.status_code, 200)
        issue_id = res.json()["id"]

        # PWD Officer triages with CONFIRM
        triage_payload = {
            "decision": "CONFIRM",
            "notes": "Field supervisor verified pothole severity."
        }
        res_triage = self.client.post(f"/api/v1/issues/{issue_id}/triage", json=triage_payload, headers=self.pwd_officer_headers)
        self.assertEqual(res_triage.status_code, 200)

        # Simulate complete application restart and clean session reload
        fresh_engine = create_engine(self.test_db_url, connect_args={"check_same_thread": False})
        FreshSession = sessionmaker(autocommit=False, autoflush=False, bind=fresh_engine)
        fresh_db = FreshSession()

        try:
            reloaded_issue = (
                fresh_db.query(Issue)
                .options(
                    joinedload(Issue.images),
                    joinedload(Issue.department),
                    joinedload(Issue.assigned_officer),
                    joinedload(Issue.reporter),
                    joinedload(Issue.status_history).joinedload(IssueStatusHistory.changed_by)
                )
                .filter(Issue.id == issue_id)
                .first()
            )
            self.assertIsNotNone(reloaded_issue)

            # 1. Verification fields persist in DB
            self.assertEqual(reloaded_issue.verified_category, "Pothole")
            self.assertEqual(reloaded_issue.status, IssueStatus.UNDER_REVIEW)

            # 2. Dynamic properties evaluate safely without in-memory dependency
            self.assertTrue(reloaded_issue.is_verified)
            self.assertEqual(reloaded_issue.verification_status, "CONFIRMED")
            self.assertEqual(reloaded_issue.ai_suggested_category, "Pothole")
            self.assertEqual(reloaded_issue.last_reviewed_by_name, "PWD Inspector")
            self.assertIsNotNone(reloaded_issue.last_reviewed_at)

            # 3. Pydantic schema serialization succeeds and preserves all verification attributes
            pydantic_out = IssueDetailOut.model_validate(reloaded_issue)
            self.assertTrue(pydantic_out.is_verified)
            self.assertEqual(pydantic_out.verification_status, "CONFIRMED")
            self.assertEqual(pydantic_out.verified_category, "Pothole")
            self.assertEqual(pydantic_out.ai_suggested_category, "Pothole")
            self.assertEqual(pydantic_out.last_reviewed_by_name, "PWD Inspector")
            self.assertIsNotNone(pydantic_out.last_reviewed_at)
        finally:
            fresh_db.close()
            fresh_engine.dispose()

    # -------------------------------------------------------------------------
    # Scenario 12: Repeated triage requests idempotency and duplicate history prevention
    # -------------------------------------------------------------------------
    def test_12_repeated_triage_requests_idempotency_and_no_duplicate_history(self):
        payload = {
            "title": "Repeated Triage Test",
            "issue_type": "Pothole",
            "latitude": 28.6175,
            "longitude": 77.2125,
            "original_image_url": "/uploads/original/repeated.jpg",
            "ai_confidence": 0.81,
            "severity": "HIGH",
            "priority_score": 70.0,
            "ai_analysis_status": "SUCCESS"
        }
        res = self.client.post("/api/v1/issues", json=payload, headers=self.citizen_headers)
        issue_id = res.json()["id"]

        triage_body = {
            "decision": "CONFIRM",
            "notes": "Verified by officer"
        }

        # First call
        res1 = self.client.post(f"/api/v1/issues/{issue_id}/triage", json=triage_body, headers=self.pwd_officer_headers)
        self.assertEqual(res1.status_code, 200)

        session = self.SessionLocal()
        h_count_1 = session.query(IssueStatusHistory).filter_by(issue_id=issue_id).count()
        session.close()

        # Second identical call (simulate accidental double-click / network retry)
        res2 = self.client.post(f"/api/v1/issues/{issue_id}/triage", json=triage_body, headers=self.pwd_officer_headers)
        self.assertEqual(res2.status_code, 200)

        session = self.SessionLocal()
        h_count_2 = session.query(IssueStatusHistory).filter_by(issue_id=issue_id).count()
        session.close()

        # Duplicate history must NOT be created without explicit reason
        self.assertEqual(h_count_1, h_count_2)

        # Third call with new notes (explicit reason) MUST create an audit history entry
        triage_new_note = {
            "decision": "CONFIRM",
            "notes": "Second inspector re-confirmed on site with depth measurement."
        }
        res3 = self.client.post(f"/api/v1/issues/{issue_id}/triage", json=triage_new_note, headers=self.pwd_officer_headers)
        self.assertEqual(res3.status_code, 200)

        session = self.SessionLocal()
        h_count_3 = session.query(IssueStatusHistory).filter_by(issue_id=issue_id).count()
        session.close()
        self.assertEqual(h_count_3, h_count_1 + 1)

    # -------------------------------------------------------------------------
    # Scenario 13: State transitions and contradiction safety
    # -------------------------------------------------------------------------
    def test_13_state_transitions_and_contradiction_safety(self):
        payload = {
            "title": "Reclassification after False Positive Rejection",
            "issue_type": "Pothole",
            "latitude": 28.6180,
            "longitude": 77.2130,
            "original_image_url": "/uploads/original/reclass.jpg",
            "ai_confidence": 0.77,
            "severity": "HIGH",
            "priority_score": 65.0,
            "ai_analysis_status": "SUCCESS"
        }
        res = self.client.post("/api/v1/issues", json=payload, headers=self.citizen_headers)
        issue_id = res.json()["id"]

        # Step 1: Reject suggestion
        res_reject = self.client.post(
            f"/api/v1/issues/{issue_id}/triage",
            json={"decision": "REJECT_SUGGESTION", "notes": "Initial reviewer believed this was water stain."},
            headers=self.pwd_officer_headers
        )
        self.assertEqual(res_reject.status_code, 200)
        data_rej = res_reject.json()
        self.assertEqual(data_rej["verification_status"], "REJECTED")
        self.assertEqual(data_rej["ai_analysis_status"], "AI_SUGGESTION_REJECTED")

        # Step 2: Second officer inspects and corrects to Alligator Crack
        res_correct = self.client.post(
            f"/api/v1/issues/{issue_id}/triage",
            json={"decision": "CORRECT", "verified_category": "Alligator Crack", "notes": "Senior engineer confirmed extensive pavement fatigue cracking."},
            headers=self.pwd_officer_headers
        )
        self.assertEqual(res_correct.status_code, 200)
        data_corr = res_correct.json()

        # ai_analysis_status must reset to SUCCESS, not remain in conflicting AI_SUGGESTION_REJECTED
        self.assertEqual(data_corr["ai_analysis_status"], "SUCCESS")
        self.assertTrue(data_corr["is_verified"])
        self.assertEqual(data_corr["verification_status"], "CORRECTED")
        self.assertEqual(data_corr["verified_category"], "Alligator Crack")
        # Original category is preserved
        self.assertEqual(data_corr["ai_suggested_category"], "Pothole")

    # -------------------------------------------------------------------------
    # Scenario 14: Invalid, tampered, and cross-department access safety
    # -------------------------------------------------------------------------
    def test_14_invalid_tampered_and_cross_department_access_safety(self):
        payload = {
            "title": "Auth Safety Pothole",
            "issue_type": "Pothole",
            "latitude": 28.6185,
            "longitude": 77.2135,
            "original_image_url": "/uploads/original/tamper.jpg",
            "ai_confidence": 0.80,
            "severity": "HIGH",
            "priority_score": 72.0,
            "ai_analysis_status": "SUCCESS"
        }
        res = self.client.post("/api/v1/issues", json=payload, headers=self.citizen_headers)
        issue_id = res.json()["id"]

        session = self.SessionLocal()
        initial_history_count = session.query(IssueStatusHistory).filter_by(issue_id=issue_id).count()
        session.close()

        # 1. Non-existent issue ID -> 404 Not Found
        res_404 = self.client.post("/api/v1/issues/999999/triage", json={"decision": "CONFIRM"}, headers=self.admin_headers)
        self.assertEqual(res_404.status_code, 404)

        # 2. Tampered ID: Officer from sanitation tries to triage PWD issue -> 403 Forbidden
        res_tamper = self.client.post(f"/api/v1/issues/{issue_id}/triage", json={"decision": "CONFIRM"}, headers=self.san_officer_headers)
        self.assertEqual(res_tamper.status_code, 403)

        # 3. Invalid triage decision -> 422 Unprocessable Entity
        res_bad_dec = self.client.post(f"/api/v1/issues/{issue_id}/triage", json={"decision": "DESTROY"}, headers=self.pwd_officer_headers)
        self.assertEqual(res_bad_dec.status_code, 422)

        # 4. Invalid defect category on CORRECT -> 400 Bad Request
        res_bad_cat = self.client.post(
            f"/api/v1/issues/{issue_id}/triage",
            json={"decision": "CORRECT", "verified_category": "NonExistentDefect", "notes": "Attempt with fake category"},
            headers=self.pwd_officer_headers
        )
        self.assertEqual(res_bad_cat.status_code, 400)

        # 5. Missing notes on REJECT_SUGGESTION -> 400 Bad Request
        res_no_notes = self.client.post(
            f"/api/v1/issues/{issue_id}/triage",
            json={"decision": "REJECT_SUGGESTION", "notes": ""},
            headers=self.pwd_officer_headers
        )
        self.assertEqual(res_no_notes.status_code, 400)

        # 6. Missing notes on REQUEST_INFO -> 400 Bad Request
        res_no_info_notes = self.client.post(
            f"/api/v1/issues/{issue_id}/triage",
            json={"decision": "REQUEST_INFO", "notes": "  "},
            headers=self.pwd_officer_headers
        )
        self.assertEqual(res_no_info_notes.status_code, 400)

        # 7. Missing verified_category on CORRECT -> 400 Bad Request
        res_no_corr_cat = self.client.post(
            f"/api/v1/issues/{issue_id}/triage",
            json={"decision": "CORRECT", "notes": "Forgot to provide category"},
            headers=self.pwd_officer_headers
        )
        self.assertEqual(res_no_corr_cat.status_code, 400)

        # Ensure NO audit history entries were recorded from any failed attempt
        session = self.SessionLocal()
        final_history_count = session.query(IssueStatusHistory).filter_by(issue_id=issue_id).count()
        issue_state = session.query(Issue).filter_by(id=issue_id).first()
        self.assertEqual(initial_history_count, final_history_count)
        self.assertFalse(issue_state.is_verified)
        self.assertIsNone(issue_state.verified_category)
        session.close()

    # -------------------------------------------------------------------------
    # Scenario 15: Reviewer identity ordering, non-review history immunity, and fallback
    # -------------------------------------------------------------------------
    def test_15_reviewer_identity_ordering_and_non_review_history_immunity(self):
        payload = {
            "title": "Multi-Review Ordering Test",
            "issue_type": "Pothole",
            "latitude": 28.6190,
            "longitude": 77.2140,
            "original_image_url": "/uploads/original/multi_review.jpg",
            "ai_confidence": 0.85,
            "severity": "HIGH",
            "priority_score": 75.0,
            "ai_analysis_status": "SUCCESS"
        }
        res = self.client.post("/api/v1/issues", json=payload, headers=self.citizen_headers)
        issue_id = res.json()["id"]

        # Step 1: First review by Municipal Admin (CONFIRM)
        res_rev1 = self.client.post(
            f"/api/v1/issues/{issue_id}/triage",
            json={"decision": "CONFIRM", "notes": "Admin initial review."},
            headers=self.admin_headers
        )
        self.assertEqual(res_rev1.status_code, 200)
        data_rev1 = res_rev1.json()
        self.assertEqual(data_rev1["last_reviewed_by_name"], "Municipal Administrator")
        rev1_time = data_rev1["last_reviewed_at"]
        self.assertIsNotNone(rev1_time)

        # Step 2: Second review by PWD Officer (CORRECT to Longitudinal Crack)
        res_rev2 = self.client.post(
            f"/api/v1/issues/{issue_id}/triage",
            json={"decision": "CORRECT", "verified_category": "Longitudinal Crack", "notes": "Field engineer reclassification."},
            headers=self.pwd_officer_headers
        )
        self.assertEqual(res_rev2.status_code, 200)
        data_rev2 = res_rev2.json()
        # Must reflect the latest reviewer and latest review timestamp
        self.assertEqual(data_rev2["last_reviewed_by_name"], "PWD Inspector")
        self.assertEqual(data_rev2["verified_category"], "Longitudinal Crack")
        self.assertEqual(data_rev2["verification_status"], "CORRECTED")

        # Step 3: Subsequent non-review mutations must NOT overwrite reviewer metadata
        # E.g. Progress update note
        res_prog = self.client.post(
            f"/api/v1/issues/{issue_id}/notes",
            json={"progress_percentage": 30, "note": "Contractor dispatched to site."},
            headers=self.pwd_officer_headers
        )
        self.assertEqual(res_prog.status_code, 200)
        data_prog = res_prog.json()
        # Reviewer metadata must still identify PWD Inspector and the triage review timestamp
        self.assertEqual(data_prog["last_reviewed_by_name"], "PWD Inspector")
        self.assertEqual(data_prog["last_reviewed_at"], data_rev2["last_reviewed_at"])

        # Step 4: Verify detached resolution fallback
        session = self.SessionLocal()
        raw_issue = session.query(Issue).filter_by(id=issue_id).first()
        self.assertIsNotNone(raw_issue)
        # Detached property evaluation
        self.assertEqual(raw_issue.last_reviewed_by_name, "PWD Inspector")
        self.assertIsNotNone(raw_issue.last_reviewed_at)
        session.close()


if __name__ == "__main__":
    unittest.main()


