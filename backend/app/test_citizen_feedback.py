"""
CivicVision AI — Phase 5: Citizen Feedback and Clarification Workflow Test Suite
==================================================================================

Focused regression tests covering all 8 mandated scenarios:
1. Citizen viewing only their own clarification requests and responses.
2. Citizen responding to their own request.
3. Attempts to respond to another citizen's request being rejected (403 Forbidden).
4. Unauthorized users being unable to issue review requests.
5. Clarification history persisting across separate database sessions.
6. Citizen responses not automatically verifying or resolving reports.
7. Report history and original AI metadata remaining intact.
8. Existing authentication, department authorization, and triage behavior remaining unchanged.
"""

import os
import sys
import json
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
from app.core.database import Base, get_db
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.issue import Issue, IssueStatus, IssueType, SeverityLevel
from app.models.history import IssueStatusHistory
from app.models.clarification import IssueClarification
from app.schemas.issue import IssueDetailOut
from app.core.security import get_password_hash


class TestCitizenFeedbackWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp(prefix="civicvision_citizen_feedback_test_")
        cls.test_db_path = os.path.join(cls.temp_dir, "citizen_feedback_test.db")
        cls.test_db_url = f"sqlite:///{cls.test_db_path}"

        # Safety: ensure production DB is never referenced
        assert "civicsense.db" not in cls.test_db_url.lower()
        assert "civicvision.db" not in cls.test_db_url.lower()

        cls.engine = create_engine(cls.test_db_url, connect_args={"check_same_thread": False})
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

        session = cls.SessionLocal()

        # Seed departments
        cls.dept_pwd = Department(name="Road & Public Works Department", code="DEPT_PWD", description="Roads")
        cls.dept_san = Department(name="Waste Management & Sanitation Dept", code="DEPT_SAN", description="Sanitation")
        session.add_all([cls.dept_pwd, cls.dept_san])
        session.commit()

        # Seed users: 2 citizens, 1 admin, 1 PWD officer, 1 Sanitation officer
        cls.citizen_1 = User(
            full_name="Citizen One",
            email="citizen1.fb@civicvision.ai",
            hashed_password=get_password_hash("TestPass@123"),
            role=UserRole.CITIZEN
        )
        cls.citizen_2 = User(
            full_name="Citizen Two",
            email="citizen2.fb@civicvision.ai",
            hashed_password=get_password_hash("TestPass@123"),
            role=UserRole.CITIZEN
        )
        cls.admin = User(
            full_name="Municipal Administrator",
            email="admin.fb@civicvision.ai",
            hashed_password=get_password_hash("TestPass@123"),
            role=UserRole.ADMIN
        )
        cls.officer_pwd = User(
            full_name="PWD Inspector",
            email="officer.pwd.fb@civicvision.ai",
            hashed_password=get_password_hash("TestPass@123"),
            role=UserRole.OFFICER,
            department_id=cls.dept_pwd.id
        )
        cls.officer_san = User(
            full_name="Sanitation Inspector",
            email="officer.san.fb@civicvision.ai",
            hashed_password=get_password_hash("TestPass@123"),
            role=UserRole.OFFICER,
            department_id=cls.dept_san.id
        )
        session.add_all([cls.citizen_1, cls.citizen_2, cls.admin, cls.officer_pwd, cls.officer_san])
        session.commit()

        cls.citizen_1_id = cls.citizen_1.id
        cls.citizen_2_id = cls.citizen_2.id
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
        r1 = cls.client.post("/api/v1/auth/login", json={"email": "citizen1.fb@civicvision.ai", "password": "TestPass@123"})
        cls.c1_headers = {"Authorization": f"Bearer {r1.json()['access_token']}"}

        r2 = cls.client.post("/api/v1/auth/login", json={"email": "citizen2.fb@civicvision.ai", "password": "TestPass@123"})
        cls.c2_headers = {"Authorization": f"Bearer {r2.json()['access_token']}"}

        ra = cls.client.post("/api/v1/auth/login", json={"email": "admin.fb@civicvision.ai", "password": "TestPass@123"})
        cls.admin_headers = {"Authorization": f"Bearer {ra.json()['access_token']}"}

        ro = cls.client.post("/api/v1/auth/login", json={"email": "officer.pwd.fb@civicvision.ai", "password": "TestPass@123"})
        cls.pwd_headers = {"Authorization": f"Bearer {ro.json()['access_token']}"}

        rs = cls.client.post("/api/v1/auth/login", json={"email": "officer.san.fb@civicvision.ai", "password": "TestPass@123"})
        cls.san_headers = {"Authorization": f"Bearer {rs.json()['access_token']}"}

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def _create_sample_issue(self, citizen_headers, title="Pothole on Main Rd"):
        payload = {
            "title": title,
            "description": "Deep hole near intersection.",
            "issue_type": "Pothole",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "address": "Intersection of Main Rd and 5th St",
            "original_image_url": "/uploads/original/pothole.jpg",
            "ai_confidence": 0.84,
            "severity": "HIGH",
            "priority_score": 72.0,
            "bounding_box_json": json.dumps([{"class": "Pothole", "x": 100, "y": 100, "width": 120, "height": 80}]),
            "detected_defects_json": json.dumps([{"category": "Pothole", "confidence": 0.84}]),
            "ai_analysis_status": "SUCCESS"
        }
        res = self.client.post("/api/v1/issues", json=payload, headers=citizen_headers)
        self.assertEqual(res.status_code, 200)
        return res.json()["id"]

    # -------------------------------------------------------------------------
    # Scenario 1: Citizen views only their own clarification requests
    # -------------------------------------------------------------------------
    def test_01_citizen_views_only_own_clarification_requests(self):
        issue_id = self._create_sample_issue(self.c1_headers, title="Issue for Clarification Auth")

        # PWD Officer requests additional information
        req_res = self.client.post(
            f"/api/v1/issues/{issue_id}/clarifications",
            json={"notes": "Please specify whether the pothole is on the northbound or southbound carriageway."},
            headers=self.pwd_headers
        )
        self.assertEqual(req_res.status_code, 200)
        clarification_id = req_res.json()["id"]

        # Citizen 1 (the report owner) can view their clarifications
        view_res = self.client.get(f"/api/v1/issues/{issue_id}/clarifications", headers=self.c1_headers)
        self.assertEqual(view_res.status_code, 200)
        clarifications = view_res.json()
        self.assertEqual(len(clarifications), 1)
        self.assertEqual(clarifications[0]["id"], clarification_id)
        self.assertEqual(clarifications[0]["status"], "PENDING")
        self.assertIn("carriageway", clarifications[0]["request_text"])

        # Citizen 2 (unrelated user) CANNOT view Citizen 1's clarifications (403 Forbidden)
        view_c2 = self.client.get(f"/api/v1/issues/{issue_id}/clarifications", headers=self.c2_headers)
        self.assertEqual(view_c2.status_code, 403)

        # Citizen 2 CANNOT view Citizen 1's issue details (403 Forbidden)
        detail_c2 = self.client.get(f"/api/v1/issues/{issue_id}", headers=self.c2_headers)
        self.assertEqual(detail_c2.status_code, 403)

        # Citizen 2 CANNOT view Citizen 1's timeline (403 Forbidden)
        timeline_c2 = self.client.get(f"/api/v1/issues/{issue_id}/timeline", headers=self.c2_headers)
        self.assertEqual(timeline_c2.status_code, 403)

    # -------------------------------------------------------------------------
    # Scenario 2: Citizen responding to their own request
    # -------------------------------------------------------------------------
    def test_02_citizen_responds_to_own_request(self):
        issue_id = self._create_sample_issue(self.c1_headers, title="Issue for Citizen Response")

        # Officer issues clarification request via triage
        triage_res = self.client.post(
            f"/api/v1/issues/{issue_id}/triage",
            json={"decision": "REQUEST_INFO", "notes": "Please provide a landmark or nearest metro pillar."},
            headers=self.pwd_headers
        )
        self.assertEqual(triage_res.status_code, 200)
        issue_data = triage_res.json()
        self.assertTrue(issue_data["has_pending_clarification"])
        self.assertEqual(len(issue_data["clarifications"]), 1)
        c_id = issue_data["clarifications"][0]["id"]

        # Citizen 1 responds
        resp_payload = {
            "response_text": "It is directly opposite Pillar 148 on Northbound carriageway.",
            "supplementary_image_url": "/uploads/original/pillar148.jpg"
        }
        resp_res = self.client.post(
            f"/api/v1/issues/{issue_id}/clarifications/{c_id}/respond",
            json=resp_payload,
            headers=self.c1_headers
        )
        self.assertEqual(resp_res.status_code, 200)
        updated_issue = resp_res.json()

        # Pending clarification is now False
        self.assertFalse(updated_issue["has_pending_clarification"])
        self.assertEqual(len(updated_issue["clarifications"]), 1)
        c_record = updated_issue["clarifications"][0]
        self.assertEqual(c_record["status"], "RESPONDED")
        self.assertIn("Pillar 148", c_record["response_text"])
        self.assertEqual(c_record["response_image_path"], "/uploads/original/pillar148.jpg")
        self.assertIsNotNone(c_record["responded_at"])

        # Supplementary image was linked
        image_paths = [img["original_image_path"] for img in updated_issue["images"]]
        self.assertIn("/uploads/original/pillar148.jpg", image_paths)

    # -------------------------------------------------------------------------
    # Scenario 3: Attempts to respond to another citizen's request rejected
    # -------------------------------------------------------------------------
    def test_03_another_citizen_cannot_respond_to_request(self):
        issue_id = self._create_sample_issue(self.c1_headers, title="Tampering Test Issue")

        # Officer requests clarification
        c_res = self.client.post(
            f"/api/v1/issues/{issue_id}/clarifications",
            json={"notes": "Please confirm if water is actively pooling."},
            headers=self.pwd_headers
        )
        c_id = c_res.json()["id"]

        # Citizen 2 attempts to respond to Citizen 1's request -> 403 Forbidden!
        tamper_res = self.client.post(
            f"/api/v1/issues/{issue_id}/clarifications/{c_id}/respond",
            json={"response_text": "Unauthorized answer from attacker."},
            headers=self.c2_headers
        )
        self.assertEqual(tamper_res.status_code, 403)

        # Department Officer also cannot respond on behalf of citizen -> 403 Forbidden!
        officer_tamper = self.client.post(
            f"/api/v1/issues/{issue_id}/clarifications/{c_id}/respond",
            json={"response_text": "Officer attempting to impersonate citizen."},
            headers=self.pwd_headers
        )
        self.assertEqual(officer_tamper.status_code, 403)

        # Non-existent clarification ID -> 404
        bad_cid_res = self.client.post(
            f"/api/v1/issues/{issue_id}/clarifications/99999/respond",
            json={"response_text": "Answer for missing clarification."},
            headers=self.c1_headers
        )
        self.assertEqual(bad_cid_res.status_code, 404)

        # Response too short (< 3 characters) -> 422
        short_res = self.client.post(
            f"/api/v1/issues/{issue_id}/clarifications/{c_id}/respond",
            json={"response_text": "ok"},
            headers=self.c1_headers
        )
        self.assertEqual(short_res.status_code, 422)

    # -------------------------------------------------------------------------
    # Scenario 4: Unauthorized users unable to issue review requests
    # -------------------------------------------------------------------------
    def test_04_unauthorized_users_cannot_issue_clarifications(self):
        issue_id = self._create_sample_issue(self.c1_headers, title="Review Auth Test")

        # 4a. Unauthenticated request -> 401 Unauthorized
        res_unauth = self.client.post(
            f"/api/v1/issues/{issue_id}/clarifications",
            json={"notes": "Unauthenticated attempt."}
        )
        self.assertEqual(res_unauth.status_code, 401)

        # 4b. Citizen cannot issue clarification requests -> 403 Forbidden
        res_cit = self.client.post(
            f"/api/v1/issues/{issue_id}/clarifications",
            json={"notes": "Citizen trying to issue official review request."},
            headers=self.c1_headers
        )
        self.assertEqual(res_cit.status_code, 403)

        # 4c. Officer from an unrelated department cannot issue request -> 403 Forbidden
        res_wrong_dept = self.client.post(
            f"/api/v1/issues/{issue_id}/clarifications",
            json={"notes": "Sanitation officer attempting to review PWD issue."},
            headers=self.san_headers
        )
        self.assertEqual(res_wrong_dept.status_code, 403)

        # 4d. Authorized PWD Officer -> 200 OK
        res_auth_pwd = self.client.post(
            f"/api/v1/issues/{issue_id}/clarifications",
            json={"notes": "Authorized PWD engineering inspection request."},
            headers=self.pwd_headers
        )
        self.assertEqual(res_auth_pwd.status_code, 200)

        # 4e. Authorized Admin -> 200 OK
        res_auth_admin = self.client.post(
            f"/api/v1/issues/{issue_id}/clarifications",
            json={"notes": "Authorized Administrator oversight inquiry."},
            headers=self.admin_headers
        )
        self.assertEqual(res_auth_admin.status_code, 200)

    # -------------------------------------------------------------------------
    # Scenario 5: Clarification history persists across separate database sessions
    # -------------------------------------------------------------------------
    def test_05_clarification_history_persists_across_separate_sessions(self):
        issue_id = self._create_sample_issue(self.c1_headers, title="Persistence Clarification Test")

        # Request info
        self.client.post(
            f"/api/v1/issues/{issue_id}/clarifications",
            json={"notes": "Round 1: Requesting proximity to school zone."},
            headers=self.pwd_headers
        )
        c_list = self.client.get(f"/api/v1/issues/{issue_id}/clarifications", headers=self.c1_headers).json()
        c1_id = c_list[0]["id"]

        # Respond to Round 1
        self.client.post(
            f"/api/v1/issues/{issue_id}/clarifications/{c1_id}/respond",
            json={"response_text": "Round 1 Response: Located 20m from DAV School Gate 2."},
            headers=self.c1_headers
        )

        # Request Round 2 (follow-up)
        self.client.post(
            f"/api/v1/issues/{issue_id}/clarifications",
            json={"notes": "Round 2: Is the school zone barricaded?"},
            headers=self.pwd_headers
        )

        # Simulate fresh connection / server restart
        fresh_engine = create_engine(self.test_db_url, connect_args={"check_same_thread": False})
        FreshSession = sessionmaker(autocommit=False, autoflush=False, bind=fresh_engine)
        fresh_db = FreshSession()

        try:
            reloaded_issue = (
                fresh_db.query(Issue)
                .options(
                    joinedload(Issue.clarifications).joinedload(IssueClarification.requested_by),
                    joinedload(Issue.status_history)
                )
                .filter_by(id=issue_id)
                .first()
            )
            self.assertIsNotNone(reloaded_issue)
            self.assertEqual(len(reloaded_issue.clarifications), 2)

            # Round 1 verification
            r1 = reloaded_issue.clarifications[0]
            self.assertEqual(r1.status, "RESPONDED")
            self.assertIn("Round 1 Response", r1.response_text)
            self.assertEqual(r1.requested_by_name, "PWD Inspector")

            # Round 2 verification
            r2 = reloaded_issue.clarifications[1]
            self.assertEqual(r2.status, "PENDING")
            self.assertIsNone(r2.response_text)
            self.assertTrue(reloaded_issue.has_pending_clarification)

            # Schema validation
            pydantic_issue = IssueDetailOut.model_validate(reloaded_issue)
            self.assertTrue(pydantic_issue.has_pending_clarification)
            self.assertEqual(len(pydantic_issue.clarifications), 2)
            self.assertEqual(pydantic_issue.clarifications[0].status, "RESPONDED")
            self.assertEqual(pydantic_issue.clarifications[1].status, "PENDING")
        finally:
            fresh_db.close()
            fresh_engine.dispose()

    # -------------------------------------------------------------------------
    # Scenario 6: Citizen responses do not automatically verify or resolve reports
    # -------------------------------------------------------------------------
    def test_06_citizen_response_does_not_verify_or_resolve(self):
        issue_id = self._create_sample_issue(self.c1_headers, title="Non-Auto-Verify Test")

        # Officer requests clarification
        c_res = self.client.post(
            f"/api/v1/issues/{issue_id}/clarifications",
            json={"notes": "Please specify depth in inches."},
            headers=self.pwd_headers
        )
        c_id = c_res.json()["id"]

        # Citizen responds
        resp = self.client.post(
            f"/api/v1/issues/{issue_id}/clarifications/{c_id}/respond",
            json={"response_text": "Depth is roughly 4 to 5 inches deep."},
            headers=self.c1_headers
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        # Strict safety requirements:
        self.assertFalse(data["is_verified"], "Citizen response must NOT mark report verified")
        self.assertEqual(data["verification_status"], "UNVERIFIED")
        self.assertIsNone(data["verified_category"])
        self.assertNotEqual(data["status"], "RESOLVED", "Citizen response must NOT resolve report")
        self.assertNotEqual(data["status"], "CLOSED", "Citizen response must NOT close report")
        self.assertEqual(data["status"], "UNDER_REVIEW")
        self.assertLess(data["progress_percentage"], 100)

    # -------------------------------------------------------------------------
    # Scenario 7: Report history and original AI metadata remain intact
    # -------------------------------------------------------------------------
    def test_07_original_ai_metadata_and_complaint_intact(self):
        issue_id = self._create_sample_issue(self.c1_headers, title="AI Metadata Preservation Test")

        # Perform multiple clarification rounds
        c_res = self.client.post(
            f"/api/v1/issues/{issue_id}/clarifications",
            json={"notes": "Need cross-street name."},
            headers=self.pwd_headers
        )
        c_id = c_res.json()["id"]

        self.client.post(
            f"/api/v1/issues/{issue_id}/clarifications/{c_id}/respond",
            json={"response_text": "Cross street is 7th Boulevard."},
            headers=self.c1_headers
        )

        res = self.client.get(f"/api/v1/issues/{issue_id}", headers=self.c1_headers)
        data = res.json()

        # Check original report & complaint fields
        self.assertEqual(data["title"], "AI Metadata Preservation Test")
        self.assertEqual(data["description"], "Deep hole near intersection.")
        self.assertEqual(data["latitude"], 28.6139)
        self.assertEqual(data["longitude"], 77.2090)
        self.assertEqual(data["address"], "Intersection of Main Rd and 5th St")

        # Check AI provenance & evidence
        self.assertEqual(data["issue_type"], "Pothole")
        self.assertEqual(data["ai_confidence"], 0.84)
        self.assertEqual(data["ai_analysis_status"], "SUCCESS")
        self.assertIn("Pothole", data["detected_defects_json"])

        # History log preserved and includes citizen response entry
        hist_notes = [h["notes"] for h in data["status_history"] if h["notes"]]
        self.assertTrue(any("Citizen clarification response" in n for n in hist_notes))

    # -------------------------------------------------------------------------
    # Scenario 8: Existing auth, triage, and department routing unchanged
    # -------------------------------------------------------------------------
    def test_08_existing_auth_triage_and_routing_unchanged(self):
        issue_id = self._create_sample_issue(self.c1_headers, title="Regression Invariance Test")

        # 1. PWD Officer confirms AI suggestion
        conf_res = self.client.post(
            f"/api/v1/issues/{issue_id}/triage",
            json={"decision": "CONFIRM", "notes": "Confirmed on site."},
            headers=self.pwd_headers
        )
        self.assertEqual(conf_res.status_code, 200)
        self.assertTrue(conf_res.json()["is_verified"])
        self.assertEqual(conf_res.json()["verification_status"], "CONFIRMED")

        # 2. Reclassification with CORRECT
        corr_res = self.client.post(
            f"/api/v1/issues/{issue_id}/triage",
            json={"decision": "CORRECT", "verified_category": "Alligator Crack", "notes": "Corrected category."},
            headers=self.pwd_headers
        )
        self.assertEqual(corr_res.status_code, 200)
        self.assertTrue(corr_res.json()["is_verified"])
        self.assertEqual(corr_res.json()["verification_status"], "CORRECTED")

        # 3. Cross-department protection
        wrong_triage = self.client.post(
            f"/api/v1/issues/{issue_id}/triage",
            json={"decision": "CONFIRM"},
            headers=self.san_headers
        )
        self.assertEqual(wrong_triage.status_code, 403)


if __name__ == "__main__":
    unittest.main()
