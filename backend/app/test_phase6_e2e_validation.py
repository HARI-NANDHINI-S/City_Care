"""
CivicVision AI — Phase 6: End-to-End Workflow Validation & Release Readiness Suite
==================================================================================

Comprehensive validation suite for:
1. Citizen manual reporting workflow (no AI, proper routing, full lifecycle).
2. Citizen image-assisted reporting workflow (AI suggestion -> Request Info -> Citizen Response -> Resumed Triage Decision).
3. AI suggestion vs Human decision demarcation.
4. Application restart / detached engine persistence verification.
5. Cross-citizen and cross-department authorization enforcement.
6. Input validation, error handling, image-upload extension checking & path traversal protection.
7. Verification of all 12 defect categories and zero synthetic bounding box fabrication.
8. Model governance checks (ENABLE_IRDID_CLASSIFIER=False, checkpoint integrity).

All tests execute on isolated temporary SQLite databases without touching production data.
"""

import os
import sys
import io
import json
import uuid
import hashlib
import tempfile
import shutil
import unittest
from pathlib import Path
from PIL import Image

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.core.database import Base, get_db
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.issue import Issue, IssueStatus, IssueType, SeverityLevel
from app.models.history import IssueStatusHistory
from app.models.clarification import IssueClarification
from app.schemas.issue import IssueDetailOut
from app.core.security import get_password_hash
from app.core.defect_registry import ACTIVE_12_CATEGORIES, DEFECT_REGISTRY


class TestPhase6E2EValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp(prefix="civicvision_phase6_val_")
        cls.test_db_path = os.path.join(cls.temp_dir, "phase6_val.db")
        cls.test_db_url = f"sqlite:///{cls.test_db_path}"

        # Safety assertions
        assert "civicsense.db" not in cls.test_db_url.lower()
        assert "civicvision.db" not in cls.test_db_url.lower()

        cls.engine = create_engine(cls.test_db_url, connect_args={"check_same_thread": False})
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

        session = cls.SessionLocal()

        # Seed municipal departments
        cls.dept_pwd = Department(name="Road & Public Works Department", code="DEPT_PWD", description="Roads")
        cls.dept_san = Department(name="Waste Management & Sanitation Dept", code="DEPT_SAN", description="Sanitation")
        cls.dept_drain = Department(name="Stormwater & Drainage Department", code="DEPT_DRAIN", description="Drainage")
        cls.dept_elec = Department(name="Electrical Infrastructure Dept", code="DEPT_ELEC", description="Electrical")
        cls.dept_sew = Department(name="Sewerage & Sanitation Board", code="DEPT_SEW", description="Sewerage")
        session.add_all([cls.dept_pwd, cls.dept_san, cls.dept_drain, cls.dept_elec, cls.dept_sew])
        session.commit()

        # Seed users across roles & departments
        cls.citizen_a = User(
            full_name="Citizen Alpha",
            email="citizen.alpha@civicvision.ai",
            hashed_password=get_password_hash("Pass@123"),
            role=UserRole.CITIZEN
        )
        cls.citizen_b = User(
            full_name="Citizen Beta",
            email="citizen.beta@civicvision.ai",
            hashed_password=get_password_hash("Pass@123"),
            role=UserRole.CITIZEN
        )
        cls.admin = User(
            full_name="Lead Municipal Admin",
            email="admin.phase6@civicvision.ai",
            hashed_password=get_password_hash("Pass@123"),
            role=UserRole.ADMIN
        )
        cls.officer_pwd = User(
            full_name="PWD Officer Dave",
            email="officer.pwd.p6@civicvision.ai",
            hashed_password=get_password_hash("Pass@123"),
            role=UserRole.OFFICER,
            department_id=cls.dept_pwd.id
        )
        cls.officer_san = User(
            full_name="Sanitation Officer Sarah",
            email="officer.san.p6@civicvision.ai",
            hashed_password=get_password_hash("Pass@123"),
            role=UserRole.OFFICER,
            department_id=cls.dept_san.id
        )
        session.add_all([cls.citizen_a, cls.citizen_b, cls.admin, cls.officer_pwd, cls.officer_san])
        session.commit()

        cls.citizen_a_id = cls.citizen_a.id
        cls.citizen_b_id = cls.citizen_b.id
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

        # Authenticate users
        cls.token_ca = cls._login("citizen.alpha@civicvision.ai", "Pass@123")
        cls.token_cb = cls._login("citizen.beta@civicvision.ai", "Pass@123")
        cls.token_admin = cls._login("admin.phase6@civicvision.ai", "Pass@123")
        cls.token_pwd = cls._login("officer.pwd.p6@civicvision.ai", "Pass@123")
        cls.token_san = cls._login("officer.san.p6@civicvision.ai", "Pass@123")

        cls.ca_headers = {"Authorization": f"Bearer {cls.token_ca}"}
        cls.cb_headers = {"Authorization": f"Bearer {cls.token_cb}"}
        cls.admin_headers = {"Authorization": f"Bearer {cls.token_admin}"}
        cls.pwd_headers = {"Authorization": f"Bearer {cls.token_pwd}"}
        cls.san_headers = {"Authorization": f"Bearer {cls.token_san}"}

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        cls.engine.dispose()
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    @classmethod
    def _login(cls, email: str, password: str) -> str:
        res = cls.client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert res.status_code == 200, f"Login failed for {email}: {res.text}"
        return res.json()["access_token"]

    # -------------------------------------------------------------------------
    # Check 1: Manual Report End-to-End Lifecycle
    # -------------------------------------------------------------------------
    def test_01_manual_report_lifecycle_end_to_end(self):
        """Citizen submits manual report without AI; department officer advances to resolution."""
        payload = {
            "title": "Overflowing Community Garbage Bin",
            "description": "Large garbage container overflowing near community center.",
            "issue_type": "Overflowing Garbage Bins",
            "latitude": 28.5355,
            "longitude": 77.3910,
            "address": "Community Center Road, Block C",
            "original_image_url": "/uploads/manual/overflow_bin.jpg",
            "ai_confidence": 0.0,
            "severity": "HIGH",
            "priority_score": 70.0,
            "bounding_box_json": "[]",
            "detected_defects_json": "[]",
            "ai_analysis_status": "MANUAL"
        }
        create_res = self.client.post("/api/v1/issues", json=payload, headers=self.ca_headers)
        self.assertEqual(create_res.status_code, 200)
        issue = create_res.json()
        issue_id = issue["id"]

        # Initial workflow state: starts in REPORTED
        self.assertEqual(issue["status"], "REPORTED")
        self.assertFalse(issue["is_verified"])
        self.assertEqual(issue["verification_status"], "UNVERIFIED")
        self.assertEqual(issue["department"]["code"], "DEPT_SAN")

        # Officer of assigned department accepts report
        accept_res = self.client.post(f"/api/v1/issues/{issue_id}/accept", headers=self.san_headers)
        self.assertEqual(accept_res.status_code, 200)
        self.assertEqual(accept_res.json()["status"], "UNDER_REVIEW")

        # Officer updates progress
        prog_res = self.client.patch(
            f"/api/v1/issues/{issue_id}/progress",
            json={"progress_percentage": 50, "note": "Sanitation crew dispatched to clear bin."},
            headers=self.san_headers
        )
        self.assertEqual(prog_res.status_code, 200)
        self.assertEqual(prog_res.json()["status"], "IN_PROGRESS")
        self.assertEqual(prog_res.json()["progress_percentage"], 50)

        # Officer resolves report
        resolve_res = self.client.patch(
            f"/api/v1/issues/{issue_id}/status",
            json={"status": "RESOLVED", "notes": "Bin emptied and area disinfected."},
            headers=self.san_headers
        )
        self.assertEqual(resolve_res.status_code, 200)
        self.assertEqual(resolve_res.json()["status"], "RESOLVED")
        self.assertEqual(resolve_res.json()["progress_percentage"], 100)

        # Audit timeline reflects all steps in order
        time_res = self.client.get(f"/api/v1/issues/{issue_id}/timeline", headers=self.ca_headers)
        self.assertEqual(time_res.status_code, 200)
        timeline = time_res.json()
        statuses = [t["new_status"] for t in timeline]
        self.assertIn("REPORTED", statuses)
        self.assertIn("UNDER_REVIEW", statuses)
        self.assertIn("IN_PROGRESS", statuses)
        self.assertIn("RESOLVED", statuses)

    # -------------------------------------------------------------------------
    # Check 2: Image-Assisted Report with Clarification Cycle & Resumed Triage
    # -------------------------------------------------------------------------
    def test_02_image_assisted_report_with_clarification_and_resumed_triage(self):
        """Image-assisted report with AI detection -> Clarification request -> Citizen response -> Resumed verification decision."""
        # Step A: Citizen Alpha creates image-assisted report
        payload = {
            "title": "Severe Pothole on Express Highway",
            "description": "Hazardous crater in left lane.",
            "issue_type": "Pothole",
            "latitude": 28.7041,
            "longitude": 77.1025,
            "address": "Express Highway KM 14",
            "original_image_url": "/uploads/original/pothole_km14.jpg",
            "annotated_image_url": "/uploads/annotated/pothole_km14_box.jpg",
            "ai_confidence": 0.88,
            "severity": "CRITICAL",
            "priority_score": 88.0,
            "bounding_box_json": json.dumps([{"box_2d": [100, 120, 350, 400], "label": "Pothole", "confidence": 0.88}]),
            "detected_defects_json": json.dumps(["Pothole"]),
            "model_provenance_json": json.dumps({"model": "yolov8-rdd2020", "source": "YOLO_OBJECT_DETECTION"}),
            "ai_analysis_status": "SUCCESS"
        }
        create_res = self.client.post("/api/v1/issues", json=payload, headers=self.ca_headers)
        self.assertEqual(create_res.status_code, 200)
        issue = create_res.json()
        issue_id = issue["id"]

        # AI suggestion state: starts in AI_ANALYZED, clearly UNVERIFIED
        self.assertEqual(issue["status"], "AI_ANALYZED")
        self.assertFalse(issue["is_verified"])
        self.assertEqual(issue["verification_status"], "UNVERIFIED")
        self.assertIsNone(issue["verified_category"])
        self.assertFalse(issue["has_pending_clarification"])

        # Step B: PWD Officer requests clarification via triage
        req_res = self.client.post(
            f"/api/v1/issues/{issue_id}/triage",
            json={"decision": "REQUEST_INFO", "notes": "Please provide landmark or nearest highway exit number."},
            headers=self.pwd_headers
        )
        self.assertEqual(req_res.status_code, 200)
        triaged_data = req_res.json()
        self.assertEqual(triaged_data["status"], "UNDER_REVIEW")
        self.assertTrue(triaged_data["has_pending_clarification"])
        self.assertFalse(triaged_data["is_verified"])

        # Step C: Verify pending clarifications visible to owner Citizen Alpha
        pending_res = self.client.get("/api/v1/issues/clarifications/pending", headers=self.ca_headers)
        self.assertEqual(pending_res.status_code, 200)
        pending_ids = [i["id"] for i in pending_res.json()]
        self.assertIn(issue_id, pending_ids)

        # Get clarification ID
        detail_res = self.client.get(f"/api/v1/issues/{issue_id}", headers=self.ca_headers)
        clarifications = detail_res.json()["clarifications"]
        self.assertEqual(len(clarifications), 1)
        clarification_id = clarifications[0]["id"]
        self.assertEqual(clarifications[0]["status"], "PENDING")

        # Step D: Cross-citizen unauthorized response attempt (Citizen Beta) must fail (403)
        unauth_resp = self.client.post(
            f"/api/v1/issues/{issue_id}/clarifications/{clarification_id}/respond",
            json={"response_text": "Trying to answer another citizen's report."},
            headers=self.cb_headers
        )
        self.assertEqual(unauth_resp.status_code, 403)

        # Step E: Legitimate owner (Citizen Alpha) responds with details & supplementary photo
        legit_resp = self.client.post(
            f"/api/v1/issues/{issue_id}/clarifications/{clarification_id}/respond",
            json={
                "response_text": "Nearest landmark is Exit 7B near the toll plaza.",
                "supplementary_image_url": "/uploads/clarification/exit7b_sign.jpg"
            },
            headers=self.ca_headers
        )
        self.assertEqual(legit_resp.status_code, 200)
        resp_data = legit_resp.json()

        # Strict safety checks: report is NOT verified or resolved
        self.assertFalse(resp_data["is_verified"])
        self.assertEqual(resp_data["verification_status"], "UNVERIFIED")
        self.assertEqual(resp_data["status"], "UNDER_REVIEW")
        self.assertFalse(resp_data["has_pending_clarification"])

        # Step F: Authorized reviewer resumes triage and confirms AI suggestion
        final_triage = self.client.post(
            f"/api/v1/issues/{issue_id}/triage",
            json={"decision": "CONFIRM", "notes": "Location confirmed with Exit 7B landmark."},
            headers=self.pwd_headers
        )
        self.assertEqual(final_triage.status_code, 200)
        verified_data = final_triage.json()

        # Now verified by authorized reviewer
        self.assertTrue(verified_data["is_verified"])
        self.assertEqual(verified_data["verification_status"], "CONFIRMED")
        self.assertEqual(verified_data["verified_category"], "Pothole")
        self.assertEqual(verified_data["last_reviewed_by_name"], "PWD Officer Dave")

    # -------------------------------------------------------------------------
    # Check 3: Multi-Session and Application Restart Persistence
    # -------------------------------------------------------------------------
    def test_03_restart_persistence_across_fresh_engine(self):
        """Verify that issues, verified status, reviewer metadata, and clarifications survive complete engine re-instantiation."""
        # Create an issue and complete full verification cycle
        payload = {
            "title": "Persistent Review Test",
            "description": "Deep transverse crack.",
            "issue_type": "Transverse Crack",
            "latitude": 28.6200,
            "longitude": 77.2100,
            "address": "Ring Road Sector 1",
            "original_image_url": "/uploads/test/transverse.jpg",
            "ai_confidence": 0.81,
            "severity": "HIGH",
            "priority_score": 75.0,
            "bounding_box_json": json.dumps([{"box_2d": [50, 50, 200, 200], "label": "Transverse Crack", "confidence": 0.81}]),
            "ai_analysis_status": "SUCCESS"
        }
        res = self.client.post("/api/v1/issues", json=payload, headers=self.ca_headers)
        issue_id = res.json()["id"]

        # Request clarification
        c_res = self.client.post(
            f"/api/v1/issues/{issue_id}/clarifications",
            json={"notes": "Which lane is affected?"},
            headers=self.pwd_headers
        )
        c_id = c_res.json()["id"]

        # Citizen responds
        self.client.post(
            f"/api/v1/issues/{issue_id}/clarifications/{c_id}/respond",
            json={"response_text": "Center lane affected."},
            headers=self.ca_headers
        )

        # Officer reclassifies to Longitudinal Crack
        self.client.post(
            f"/api/v1/issues/{issue_id}/triage",
            json={"decision": "CORRECT", "verified_category": "Longitudinal Crack", "notes": "Crack runs parallel to traffic."},
            headers=self.pwd_headers
        )

        # Simulate Application Restart: Fresh Engine & Session
        fresh_engine = create_engine(self.test_db_url, connect_args={"check_same_thread": False})
        FreshSession = sessionmaker(autocommit=False, autoflush=False, bind=fresh_engine)
        fresh_db = FreshSession()

        try:
            reloaded = fresh_db.query(Issue).options(
                joinedload(Issue.images),
                joinedload(Issue.department),
                joinedload(Issue.status_history).joinedload(IssueStatusHistory.changed_by),
                joinedload(Issue.clarifications).joinedload(IssueClarification.requested_by)
            ).filter(Issue.id == issue_id).first()

            self.assertIsNotNone(reloaded)
            self.assertTrue(reloaded.is_verified)
            self.assertEqual(reloaded.verification_status, "CORRECTED")
            self.assertEqual(reloaded.verified_category, "Longitudinal Crack")
            self.assertEqual(reloaded.last_reviewed_by_name, "PWD Officer Dave")
            self.assertFalse(reloaded.has_pending_clarification)

            # Clarification history survives restart
            self.assertEqual(len(reloaded.clarifications), 1)
            self.assertEqual(reloaded.clarifications[0].status, "RESPONDED")
            self.assertEqual(reloaded.clarifications[0].response_text, "Center lane affected.")
            self.assertEqual(reloaded.clarifications[0].requested_by_name, "PWD Officer Dave")

            # Pydantic schema validation succeeds with clean data
            schema_out = IssueDetailOut.model_validate(reloaded)
            self.assertTrue(schema_out.is_verified)
            self.assertEqual(schema_out.verification_status, "CORRECTED")
        finally:
            fresh_db.close()
            fresh_engine.dispose()

    # -------------------------------------------------------------------------
    # Check 4: Access Controls (Cross-Citizen & Cross-Department Restrictions)
    # -------------------------------------------------------------------------
    def test_04_cross_citizen_and_cross_department_access_controls(self):
        """Verify strict 403 Forbidden enforcement on all unauthorized access vectors."""
        # Create an issue owned by Citizen Alpha assigned to PWD
        payload = {
            "title": "Auth Guard Test Issue",
            "description": "Auth test defect.",
            "issue_type": "Pothole",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "address": "Secret Location",
            "original_image_url": "/uploads/test/auth.jpg",
            "ai_confidence": 0.0,
            "severity": "LOW",
            "priority_score": 30.0,
            "bounding_box_json": "[]",
            "ai_analysis_status": "MANUAL"
        }
        res = self.client.post("/api/v1/issues", json=payload, headers=self.ca_headers)
        issue_id = res.json()["id"]

        # 1. Unauthenticated requests rejected (401)
        self.assertEqual(self.client.get(f"/api/v1/issues/{issue_id}").status_code, 401)
        self.assertEqual(self.client.get(f"/api/v1/issues/{issue_id}/timeline").status_code, 401)
        self.assertEqual(self.client.get(f"/api/v1/issues/{issue_id}/clarifications").status_code, 401)

        # 2. Citizen Beta cannot read Citizen Alpha's issue details (403)
        self.assertEqual(self.client.get(f"/api/v1/issues/{issue_id}", headers=self.cb_headers).status_code, 403)

        # 3. Citizen Beta cannot read Citizen Alpha's timeline (403)
        self.assertEqual(self.client.get(f"/api/v1/issues/{issue_id}/timeline", headers=self.cb_headers).status_code, 403)

        # 4. Citizen Beta cannot read Citizen Alpha's clarification requests (403)
        self.assertEqual(self.client.get(f"/api/v1/issues/{issue_id}/clarifications", headers=self.cb_headers).status_code, 403)

        # 5. Sanitation Officer cannot access or triage PWD issue (403)
        self.assertEqual(self.client.get(f"/api/v1/issues/{issue_id}", headers=self.san_headers).status_code, 403)
        self.assertEqual(self.client.post(f"/api/v1/issues/{issue_id}/accept", headers=self.san_headers).status_code, 403)
        self.assertEqual(self.client.post(f"/api/v1/issues/{issue_id}/triage", json={"decision": "CONFIRM"}, headers=self.san_headers).status_code, 403)
        self.assertEqual(self.client.post(f"/api/v1/issues/{issue_id}/clarifications", json={"notes": "Illegal inquiry"}, headers=self.san_headers).status_code, 403)

        # 6. Citizen Alpha cannot triage their own issue (403)
        self.assertEqual(self.client.post(f"/api/v1/issues/{issue_id}/triage", json={"decision": "CONFIRM"}, headers=self.ca_headers).status_code, 403)

    # -------------------------------------------------------------------------
    # Check 5: Input Validation & Image Upload Security
    # -------------------------------------------------------------------------
    def test_05_input_validation_and_image_upload_security(self):
        """Verify strict extension whitelist, path traversal protection, and payload validation."""
        # 1. Disallowed file extensions (.exe, .sh, .pdf, .php) rejected (400)
        for bad_ext in ["malware.exe", "script.sh", "doc.pdf", "shell.php"]:
            fake_file = io.BytesIO(b"fake binary payload")
            res = self.client.post(
                "/api/v1/issues/analyze-image",
                files={"file": (bad_ext, fake_file, "application/octet-stream")},
                headers=self.ca_headers
            )
            self.assertEqual(res.status_code, 400, f"Disallowed extension {bad_ext} should return 400")
            self.assertIn("Invalid image format", res.json()["detail"])

        # 2. Path traversal attempts in filename sanitized safely
        # Server must not write outside upload dir; name is UUID-based
        img_bytes = io.BytesIO()
        Image.new("RGB", (100, 100), color=(128, 128, 128)).save(img_bytes, format="JPEG")
        img_bytes.seek(0)

        traversal_name = "../../evil_traversal.jpg"
        upload_res = self.client.post(
            "/api/v1/issues/analyze-image",
            files={"file": (traversal_name, img_bytes, "image/jpeg")},
            headers=self.ca_headers
        )
        self.assertEqual(upload_res.status_code, 200)
        uploaded_url = upload_res.json()["original_image_url"]
        # URL must be a clean UUID-based path, not containing '../'
        self.assertNotIn("..", uploaded_url)
        self.assertTrue(uploaded_url.startswith("/uploads/original/"))

        # 3. Clarification notes validation (min length 3 characters)
        issue_id = self._create_test_issue("Validation Guard Issue")
        too_short_res = self.client.post(
            f"/api/v1/issues/{issue_id}/clarifications",
            json={"notes": "ab"},
            headers=self.pwd_headers
        )
        self.assertEqual(too_short_res.status_code, 422)  # Pydantic validation error

        # 4. Invalid defect category rejection
        bad_cat_res = self.client.post(
            f"/api/v1/issues/{issue_id}/triage",
            json={"decision": "CORRECT", "verified_category": "FakeCategory123"},
            headers=self.pwd_headers
        )
        self.assertEqual(bad_cat_res.status_code, 400)
        self.assertIn("Cannot reclassify to invalid category", bad_cat_res.json()["detail"])

    # -------------------------------------------------------------------------
    # Check 6: All 12 Defect Categories Manually Reportable (No Fake Boxes)
    # -------------------------------------------------------------------------
    def test_06_all_12_categories_manually_reportable_no_fake_boxes(self):
        """Verify all 12 registered categories can be manually reported without fabricated boxes."""
        self.assertEqual(len(ACTIVE_12_CATEGORIES), 12)

        for cat_name in ACTIVE_12_CATEGORIES:
            reg_info = DEFECT_REGISTRY[cat_name]
            expected_dept = reg_info["default_dept_code"]

            payload = {
                "title": f"Manual Report for {cat_name}",
                "description": f"Field reported defect: {cat_name}",
                "issue_type": cat_name,
                "latitude": 28.6139,
                "longitude": 77.2090,
                "address": "City Sector",
                "original_image_url": f"/uploads/manual/{cat_name.lower().replace(' ', '_')}.jpg",
                "ai_confidence": 0.0,
                "severity": "MEDIUM",
                "priority_score": 50.0,
                "bounding_box_json": "[]",
                "detected_defects_json": "[]",
                "ai_analysis_status": "MANUAL"
            }
            res = self.client.post("/api/v1/issues", json=payload, headers=self.ca_headers)
            self.assertEqual(res.status_code, 200, f"Manual report for {cat_name} failed: {res.text}")
            data = res.json()

            # Status must be REPORTED
            self.assertEqual(data["status"], "REPORTED")
            self.assertFalse(data["is_verified"])
            # Department routing must match registered routing
            self.assertEqual(data["department"]["code"], expected_dept, f"Incorrect department for {cat_name}")
            # Bounding boxes must remain empty (no fake bounding boxes synthesized)
            self.assertEqual(data["images"][0]["bounding_box_json"], "[]")

    # -------------------------------------------------------------------------
    # Check 7: Model Governance & Quarantined Classifier Safety
    # -------------------------------------------------------------------------
    def test_07_model_governance_and_quarantined_classifier(self):
        """Verify ENABLE_IRDID_CLASSIFIER is False and production checkpoints are intact."""
        # 1. Feature flag must be False
        self.assertFalse(settings.ENABLE_IRDID_CLASSIFIER)

        # 2. Candidate classifier must not be loaded or enabled in production adapter
        from app.services.models.classification_adapter import IRDIDClassificationAdapter
        adapter = IRDIDClassificationAdapter()
        self.assertFalse(adapter.is_enabled)
        self.assertFalse(adapter.is_available)

        # 3. Check YOLO checkpoint integrity
        yolo_path = Path(__file__).resolve().parent / "ai_model" / "yolo" / "weights" / "best.pt"
        self.assertTrue(yolo_path.exists(), f"YOLO weights artifact must exist at {yolo_path}")
        with open(yolo_path, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest()
        # Verified YOLO checkpoint hash
        self.assertEqual(h.lower(), "289e3e1765e6d2c0e0f50195e550a929d93a5cf742cf0ad650330e93107ee696")

    def _create_test_issue(self, title: str) -> int:
        payload = {
            "title": title,
            "description": "Helper issue.",
            "issue_type": "Pothole",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "address": "Sector 1",
            "original_image_url": "/uploads/test/helper.jpg",
            "ai_confidence": 0.0,
            "severity": "MEDIUM",
            "priority_score": 50.0,
            "bounding_box_json": "[]",
            "ai_analysis_status": "MANUAL"
        }
        res = self.client.post("/api/v1/issues", json=payload, headers=self.ca_headers)
        return res.json()["id"]


if __name__ == "__main__":
    unittest.main()
