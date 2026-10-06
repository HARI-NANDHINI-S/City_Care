import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.department import Department
from app.models.user import User, UserRole
from app.models.issue import Issue, IssueType, IssueStatus, SeverityLevel
from app.models.image import IssueImage
from app.models.history import IssueStatusHistory

def seed_database():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # 1. Seed Departments
        dept_data = [
            {"name": "Road & Public Works Department", "code": "DEPT_PWD", "description": "Responsible for road repair, paving, and pothole maintenance.", "email": "pwd@civicvision.ai"},
            {"name": "Waste Management & Sanitation Dept", "code": "DEPT_SAN", "description": "Manages municipal garbage collection and illegal dumping.", "email": "sanitation@civicvision.ai"},
            {"name": "Electrical Infrastructure Dept", "code": "DEPT_ELEC", "description": "Maintains streetlights, power lines, and electrical grid safety.", "email": "electrical@civicvision.ai"},
            {"name": "Stormwater Drainage Dept", "code": "DEPT_DRAIN", "description": "Handles urban waterlogging, storm drains, and flood prevention.", "email": "drainage@civicvision.ai"},
            {"name": "Sewerage & Sanitation Board", "code": "DEPT_SEW", "description": "Maintains underground sewer pipelines and open manhole covers.", "email": "sewerage@civicvision.ai"},
        ]

        dept_map = {}
        for d in dept_data:
            dept = db.query(Department).filter(Department.code == d["code"]).first()
            if not dept:
                dept = Department(
                    name=d["name"],
                    code=d["code"],
                    description=d["description"],
                    contact_email=d["email"]
                )
                db.add(dept)
                db.flush()
            dept_map[d["code"]] = dept

        db.commit()
        print("[OK] Departments seeded successfully.")

        # 2. Seed Users
        # Admin
        admin = db.query(User).filter(User.email == "admin@civicvision.ai").first()
        if not admin:
            admin = User(
                full_name="Municipal Chief Admin",
                email="admin@civicvision.ai",
                hashed_password=get_password_hash("Admin@123"),
                role=UserRole.ADMIN
            )
            db.add(admin)

        # Officers
        pwd_officer = db.query(User).filter(User.email == "pwd.officer@civicvision.ai").first()
        if not pwd_officer:
            pwd_officer = User(
                full_name="Rajesh Sharma (PWD Lead)",
                email="pwd.officer@civicvision.ai",
                hashed_password=get_password_hash("Officer@123"),
                role=UserRole.OFFICER,
                department_id=dept_map["DEPT_PWD"].id
            )
            db.add(pwd_officer)

        san_officer = db.query(User).filter(User.email == "sanitation.officer@civicvision.ai").first()
        if not san_officer:
            san_officer = User(
                full_name="Priya Patel (Sanitation Lead)",
                email="sanitation.officer@civicvision.ai",
                hashed_password=get_password_hash("Officer@123"),
                role=UserRole.OFFICER,
                department_id=dept_map["DEPT_SAN"].id
            )
            db.add(san_officer)

        # Citizen
        citizen = db.query(User).filter(User.email == "citizen@civicvision.ai").first()
        if not citizen:
            citizen = User(
                full_name="Ananya Verma",
                email="citizen@civicvision.ai",
                hashed_password=get_password_hash("Citizen@123"),
                role=UserRole.CITIZEN
            )
            db.add(citizen)

        db.commit()
        db.refresh(citizen)
        db.refresh(admin)
        print("[OK] Users seeded successfully.")

        # 3. Seed Sample Infrastructure Issues
        sample_issues = [
            {
                "title": "Hazardous Open Manhole on Main Ring Road",
                "description": "Deep open manhole without warning barricades near school crossing.",
                "type": IssueType.MANHOLE,
                "lat": 28.6139,
                "lng": 77.2090,
                "address": "Connaught Place Ring Road, Sector 4",
                "confidence": 0.96,
                "severity": SeverityLevel.CRITICAL,
                "priority": 92.5,
                "status": IssueStatus.ASSIGNED,
                "dept_code": "DEPT_SEW",
            },
            {
                "title": "Severe Pothole Cluster on Expressway",
                "description": "Large deep potholes causing vehicle tire damage and severe traffic slowdown.",
                "type": IssueType.POTHOLE,
                "lat": 28.6250,
                "lng": 77.2180,
                "address": "Barakhamba Road Crossing",
                "confidence": 0.94,
                "severity": SeverityLevel.HIGH,
                "priority": 78.0,
                "status": IssueStatus.IN_PROGRESS,
                "dept_code": "DEPT_PWD",
            },
            {
                "title": "Garbage Accumulation near Market Gate",
                "description": "Overflowing public dumpster spilling into pedestrian walk.",
                "type": IssueType.GARBAGE,
                "lat": 28.6100,
                "lng": 77.2000,
                "address": "Janpath Market South Gate",
                "confidence": 0.91,
                "severity": SeverityLevel.MEDIUM,
                "priority": 55.0,
                "status": IssueStatus.REPORTED,
                "dept_code": "DEPT_SAN",
            },
            {
                "title": "Major Waterlogging Under Flyover",
                "description": "Submerged road lane after morning rainfall blocking small cars.",
                "type": IssueType.WATERLOGGING,
                "lat": 28.6300,
                "lng": 77.2250,
                "address": "ITO Flyover Underpass",
                "confidence": 0.93,
                "severity": SeverityLevel.HIGH,
                "priority": 81.0,
                "status": IssueStatus.UNDER_REVIEW,
                "dept_code": "DEPT_DRAIN",
            },
            {
                "title": "Broken Streetlight Array on Outer Ring Road",
                "description": "Non-functional streetlights causing dark zone for night commuters.",
                "type": IssueType.STREETLIGHT,
                "lat": 28.6050,
                "lng": 77.2150,
                "address": "Lodi Road stretch",
                "confidence": 0.88,
                "severity": SeverityLevel.MEDIUM,
                "priority": 48.0,
                "status": IssueStatus.RESOLVED,
                "dept_code": "DEPT_ELEC",
            }
        ]

        for item in sample_issues:
            existing = db.query(Issue).filter(Issue.title == item["title"]).first()
            if not existing:
                iss = Issue(
                    title=item["title"],
                    description=item["description"],
                    issue_type=item["type"],
                    latitude=item["lat"],
                    longitude=item["lng"],
                    address=item["address"],
                    ai_confidence=item["confidence"],
                    severity=item["severity"],
                    priority_score=item["priority"],
                    status=item["status"],
                    reporter_id=citizen.id,
                    department_id=dept_map[item["dept_code"]].id
                )
                db.add(iss)
                db.flush()

                # Add image placeholder
                img = IssueImage(
                    issue_id=iss.id,
                    original_image_path="/uploads/original/sample_infra.jpg",
                    annotated_image_path="/uploads/annotated/sample_infra_annotated.jpg",
                    bounding_box_json='[{"class": "' + item["type"].value + '", "confidence": ' + str(item["confidence"]) + '}]'
                )
                db.add(img)

                # Add history
                hist = IssueStatusHistory(
                    issue_id=iss.id,
                    previous_status=None,
                    new_status=item["status"],
                    changed_by_user_id=admin.id,
                    notes=f"Initial seed report set to status {item['status'].value}."
                )
                db.add(hist)

        db.commit()
        print("[OK] Sample issues seeded successfully.")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
