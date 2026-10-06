import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from app.core.config import settings
from app.core.database import SessionLocal, engine, Base
from app.models.department import Department
from app.models.user import User, UserRole
from app.models.issue import Issue, IssueType, IssueStatus, SeverityLevel
from app.models.image import IssueImage
from app.models.history import IssueStatusHistory
from app.models.duplicate import DuplicateIssueRelation

def verify_database_setup():
    print("=" * 60)
    print("      CIVICVISION AI — DATABASE VERIFICATION SUITE")
    print("=" * 60)
    print(f"[+] Configured Database URL: {settings.DATABASE_URL}")

    # 1. Connection Test
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT 1"))
        print("[+] Connection Check: SUCCESSful ping response")
    except Exception as e:
        print(f"[-] Connection Check FAILED: {e}")
        return
    finally:
        db.close()

    # 2. Table Inspection Test
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    print(f"[+] Total Detected Tables: {len(existing_tables)}")
    print(f"    Tables List: {existing_tables}")

    required_tables = [
        "departments",
        "users",
        "issues",
        "issue_images",
        "issue_status_history",
        "duplicate_issue_relations"
    ]

    missing = [t for t in required_tables if t not in existing_tables]
    if missing:
        print(f"[-] Missing Required Tables: {missing}")
    else:
        print("[+] All 6 required models present in database schema.")

    # 3. Model Insert & Relationship Test
    db = SessionLocal()
    try:
        # Check or create test department
        dept = db.query(Department).filter(Department.code == "DEPT_TEST").first()
        if not dept:
            dept = Department(name="Test Verification Dept", code="DEPT_TEST", description="Verification unit")
            db.add(dept)
            db.flush()

        # Check or create test user
        user = db.query(User).filter(User.email == "test.verify@civicvision.ai").first()
        if not user:
            user = User(
                full_name="Verification Agent",
                email="test.verify@civicvision.ai",
                hashed_password="hashed_test_pw",
                role=UserRole.CITIZEN,
                department_id=dept.id
            )
            db.add(user)
            db.flush()

        # Check or create test issue
        issue = db.query(Issue).filter(Issue.title == "Test Database Integrity Check").first()
        if not issue:
            issue = Issue(
                title="Test Database Integrity Check",
                description="Automated DB model verification",
                issue_type=IssueType.POTHOLE,
                latitude=28.6139,
                longitude=77.2090,
                address="Test Location",
                ai_confidence=0.95,
                severity=SeverityLevel.HIGH,
                priority_score=75.0,
                status=IssueStatus.REPORTED,
                reporter_id=user.id,
                department_id=dept.id
            )
            db.add(issue)
            db.flush()

        db.commit()
        print("[+] Model Foreign Keys & Relationships Test: SUCCESS")

    except Exception as e:
        print(f"[-] Model Test FAILED: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    verify_database_setup()
