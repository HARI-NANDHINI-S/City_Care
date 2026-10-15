import os
import io
import unittest
from unittest.mock import patch, MagicMock
from PIL import Image

from fastapi.testclient import TestClient
from fastapi import FastAPI, status
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.api.v1.endpoints.issues import router, get_current_user
from app.core.database import Base, get_db
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.issue import Issue

def make_test_jpeg(size_bytes: int) -> bytes:
    """Generates a valid JPEG byte sequence of exactly size_bytes."""
    img = Image.new("RGB", (32, 32), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    base = buf.getvalue()
    if len(base) < size_bytes:
        pad_needed = size_bytes - len(base)
        chunks = bytearray()
        rem = pad_needed
        while rem > 0:
            overhead = 4
            if rem <= overhead:
                chunks.extend(b"\x00" * rem)
                break
            payload_len = min(rem - overhead, 65530)
            marker_len = payload_len + 2
            chunks.extend(b"\xFF\xFE" + marker_len.to_bytes(2, "big") + (b"\x00" * payload_len))
            rem -= (payload_len + overhead)
        eoi = base.rfind(b"\xFF\xD9")
        if eoi != -1:
            res = base[:eoi] + bytes(chunks) + base[eoi:]
            if len(res) < size_bytes:
                res = res + b"\x00" * (size_bytes - len(res))
            elif len(res) > size_bytes:
                res = res[:size_bytes]
            return res
    return base[:size_bytes]

class TestUploadSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.temp_dir = tempfile.mkdtemp(prefix="civicvision_upload_sec_test_")
        cls.db_path = os.path.join(cls.temp_dir, "test.db")
        cls.engine = create_engine(f"sqlite:///{cls.db_path}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=cls.engine)
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        
        # Seed test department & user
        db = cls.SessionLocal()
        cls.dept = Department(name="Roads & Public Works", code="DEPT_PWD", description="Road repairs")
        db.add(cls.dept)
        db.flush()
        
        cls.citizen = User(
            id=101,
            email="citizen_tester@civicvision.org",
            full_name="Citizen Tester",
            hashed_password="mock_hashed_password",
            role=UserRole.CITIZEN
        )
        db.add(cls.citizen)
        db.commit()
        db.close()
        
        # Build test app
        cls.app = FastAPI()
        cls.app.include_router(router, prefix=settings.API_V1_STR)
        
        def override_db():
            db = cls.SessionLocal()
            try:
                yield db
            finally:
                db.close()
                
        def override_current_user():
            db = cls.SessionLocal()
            try:
                return db.query(User).filter(User.id == 101).first()
            finally:
                db.close()
                
        cls.app.dependency_overrides[get_db] = override_db
        cls.app.dependency_overrides[get_current_user] = override_current_user
        cls.client = TestClient(cls.app)
        
        # Ensure upload directories exist
        os.makedirs(settings.ORIGINAL_IMG_DIR, exist_ok=True)
        os.makedirs(settings.ANNOTATED_IMG_DIR, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        import shutil
        cls.engine.dispose()
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def setUp(self):
        self.initial_files = set(os.listdir(settings.ORIGINAL_IMG_DIR))

    def tearDown(self):
        # Purge any test files created during test runs to preserve upload dir cleanliness
        current_files = set(os.listdir(settings.ORIGINAL_IMG_DIR))
        new_files = current_files - self.initial_files
        for fn in new_files:
            fp = os.path.join(settings.ORIGINAL_IMG_DIR, fn)
            if os.path.exists(fp):
                try:
                    os.remove(fp)
                except OSError:
                    pass

    def test_1_valid_image_below_limit_accepted(self):
        """Check 1: A valid image below the limit is accepted."""
        payload = make_test_jpeg(128 * 1024)  # 128 KiB
        res = self.client.post(
            f"{settings.API_V1_STR}/analyze-image",
            files={"file": ("pothole_normal.jpg", payload, "image/jpeg")}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("original_image_url", data)
        self.assertTrue(data["original_image_url"].startswith("/uploads/original/"))

    def test_2_image_exactly_at_configured_limit_accepted(self):
        """Check 2: An image exactly at the configured limit is handled according to documented policy (accepted)."""
        custom_limit = 256 * 1024  # 256 KiB
        original_limit = settings.MAX_UPLOAD_SIZE_BYTES
        try:
            settings.MAX_UPLOAD_SIZE_BYTES = custom_limit
            exact_payload = make_test_jpeg(custom_limit)
            self.assertEqual(len(exact_payload), custom_limit)
            
            res = self.client.post(
                f"{settings.API_V1_STR}/analyze-image",
                files={"file": ("exact_limit.jpg", exact_payload, "image/jpeg")}
            )
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertIn("original_image_url", data)
        finally:
            settings.MAX_UPLOAD_SIZE_BYTES = original_limit

    def test_3_image_exceeding_limit_rejected_with_http_413(self):
        """Check 3: An image exceeding the limit is rejected with HTTP 413."""
        custom_limit = 200 * 1024  # 200 KiB
        original_limit = settings.MAX_UPLOAD_SIZE_BYTES
        try:
            settings.MAX_UPLOAD_SIZE_BYTES = custom_limit
            oversized = make_test_jpeg(custom_limit + 1024)  # 201 KiB
            
            res = self.client.post(
                f"{settings.API_V1_STR}/analyze-image",
                files={"file": ("oversized.jpg", oversized, "image/jpeg")}
            )
            self.assertEqual(res.status_code, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
            self.assertIn("exceeds maximum allowed size", res.json()["detail"].lower())
            
            # Verify no partial file remained on disk
            after_files = set(os.listdir(settings.ORIGINAL_IMG_DIR))
            self.assertEqual(after_files - self.initial_files, set())
        finally:
            settings.MAX_UPLOAD_SIZE_BYTES = original_limit

    def test_4_misleading_content_length_cannot_bypass_limit(self):
        """Check 4: Missing or misleading Content-Length cannot bypass the limit."""
        custom_limit = 100 * 1024  # 100 KiB
        original_limit = settings.MAX_UPLOAD_SIZE_BYTES
        try:
            settings.MAX_UPLOAD_SIZE_BYTES = custom_limit
            real_oversized = make_test_jpeg(200 * 1024)  # 200 KiB
            
            # Send with spoofed Content-Length header declaring a small size (e.g. 50 bytes)
            res = self.client.post(
                f"{settings.API_V1_STR}/analyze-image",
                files={"file": ("spoofed.jpg", real_oversized, "image/jpeg")},
                headers={"Content-Length": "50"}
            )
            # Backend counts actual streaming bytes, so it MUST reject with 413
            self.assertEqual(res.status_code, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        finally:
            settings.MAX_UPLOAD_SIZE_BYTES = original_limit

    def test_5_disallowed_file_extensions_rejected(self):
        """Check 5: Disallowed file extensions remain rejected with HTTP 400."""
        for bad_name in ["script.sh", "payload.exe", "document.pdf", "data.txt"]:
            res = self.client.post(
                f"{settings.API_V1_STR}/analyze-image",
                files={"file": (bad_name, b"echo test", "application/octet-stream")}
            )
            self.assertEqual(res.status_code, 400)
            self.assertIn("Invalid image format", res.json()["detail"])
            # Zero files created
            self.assertEqual(set(os.listdir(settings.ORIGINAL_IMG_DIR)) - self.initial_files, set())

    def test_6_path_traversal_filenames_remain_harmless(self):
        """Check 6: Path traversal filenames remain harmless."""
        valid_img = make_test_jpeg(64 * 1024)
        malicious_names = [
            "../../../../etc/passwd.jpg",
            "..\\..\\..\\windows\\system32\\cmd.jpg",
            "/absolute/path/exploit.png"
        ]
        for bad_name in malicious_names:
            res = self.client.post(
                f"{settings.API_V1_STR}/analyze-image",
                files={"file": (bad_name, valid_img, "image/jpeg")}
            )
            self.assertEqual(res.status_code, 200)
            saved_url = res.json()["original_image_url"]
            self.assertTrue(saved_url.startswith("/uploads/original/"))
            self.assertNotIn("..", saved_url)
            self.assertNotIn("passwd", saved_url)
            self.assertNotIn("system32", saved_url)

    def test_7_rejected_uploads_leave_no_partial_files_or_db_records(self):
        """Check 7: Rejected uploads leave no partial files or database records."""
        db = self.SessionLocal()
        issues_before = db.query(Issue).count()
        db.close()
        
        custom_limit = 50 * 1024
        original_limit = settings.MAX_UPLOAD_SIZE_BYTES
        try:
            settings.MAX_UPLOAD_SIZE_BYTES = custom_limit
            # Rejected 1: Oversized
            res_413 = self.client.post(
                f"{settings.API_V1_STR}/analyze-image",
                files={"file": ("oversized.jpg", make_test_jpeg(100 * 1024), "image/jpeg")}
            )
            self.assertEqual(res_413.status_code, 413)
            
            # Rejected 2: Bad extension
            res_400 = self.client.post(
                f"{settings.API_V1_STR}/analyze-image",
                files={"file": ("bad.exe", b"binary", "application/octet-stream")}
            )
            self.assertEqual(res_400.status_code, 400)
            
            # Verify 0 files created
            self.assertEqual(set(os.listdir(settings.ORIGINAL_IMG_DIR)) - self.initial_files, set())
            
            # Verify 0 DB issues created
            db = self.SessionLocal()
            self.assertEqual(db.query(Issue).count(), issues_before)
            db.close()
        finally:
            settings.MAX_UPLOAD_SIZE_BYTES = original_limit

    @patch("app.api.v1.endpoints.issues.analyze_issue_image")
    def test_8_yolo_inference_not_called_for_rejected_uploads(self, mock_yolo):
        """Check 8: YOLO inference is not called for rejected uploads."""
        custom_limit = 50 * 1024
        original_limit = settings.MAX_UPLOAD_SIZE_BYTES
        try:
            settings.MAX_UPLOAD_SIZE_BYTES = custom_limit
            
            # Oversized
            self.client.post(
                f"{settings.API_V1_STR}/analyze-image",
                files={"file": ("too_big.jpg", make_test_jpeg(100 * 1024), "image/jpeg")}
            )
            mock_yolo.assert_not_called()
            
            # Bad extension
            self.client.post(
                f"{settings.API_V1_STR}/analyze-image",
                files={"file": ("malicious.bat", b"rem test", "application/octet-stream")}
            )
            mock_yolo.assert_not_called()
        finally:
            settings.MAX_UPLOAD_SIZE_BYTES = original_limit

    def test_9_cleanup_on_simulated_error(self):
        """Check 9: File handles and temporary files are cleaned up after errors."""
        with patch("builtins.open", side_effect=OSError("Disk full simulation")):
            res = self.client.post(
                f"{settings.API_V1_STR}/analyze-image",
                files={"file": ("test_error.jpg", make_test_jpeg(32 * 1024), "image/jpeg")}
            )
            self.assertEqual(res.status_code, 500)
            # Verify no partial files lingered
            self.assertEqual(set(os.listdir(settings.ORIGINAL_IMG_DIR)) - self.initial_files, set())

    def test_10_issue_creation_flow_with_uploaded_image_continues_to_pass(self):
        """Check 10: Existing upload and issue-reporting workflow continues to pass end-to-end."""
        # 1. Upload valid image
        res_up = self.client.post(
            f"{settings.API_V1_STR}/analyze-image",
            files={"file": ("valid_pothole.jpg", make_test_jpeg(64 * 1024), "image/jpeg")}
        )
        self.assertEqual(res_up.status_code, 200)
        img_url = res_up.json()["original_image_url"]
        
        # 2. Submit report using uploaded image URL
        issue_payload = {
            "title": "Road Defect Verified",
            "description": "Pothole verified in safe upload pipeline",
            "issue_type": "Pothole",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "address": "Connaught Place Ring Road",
            "original_image_url": img_url,
            "severity": "HIGH",
            "priority_score": 80.0
        }
        res_create = self.client.post(f"{settings.API_V1_STR}", json=issue_payload)
        self.assertEqual(res_create.status_code, 200)
        issue_data = res_create.json()
        self.assertEqual(issue_data["title"], "Road Defect Verified")
        self.assertIsNotNone(issue_data["id"])

if __name__ == "__main__":
    unittest.main()
