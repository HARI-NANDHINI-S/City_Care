from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base

class IssueType(str, enum.Enum):
    # Road-related defects (5)
    POTHOLE = "Pothole"
    LONGITUDINAL_CRACK = "Longitudinal Crack"
    TRANSVERSE_CRACK = "Transverse Crack"
    ALLIGATOR_CRACK = "Alligator Crack"
    DAMAGED_ROAD_SURFACE = "Damaged Road Surface"
    # Legacy umbrella road defect
    ROAD_DAMAGE = "Road Damage"

    # Sanitation defects (3)
    GARBAGE = "Garbage Accumulation"
    ILLEGAL_DUMPING = "Illegal Dumping"
    OVERFLOWING_BINS = "Overflowing Garbage Bins"

    # Drainage defects (4)
    BLOCKED_DRAIN = "Blocked Drains"
    OVERFLOWING_DRAIN = "Overflowing Drains"
    WATERLOGGING = "Waterlogging"
    DAMAGED_DRAINAGE_COVER = "Damaged Drainage Covers"

    # Infrastructure utility defects
    STREETLIGHT = "Broken Streetlight"
    MANHOLE = "Open Manhole"

class IssueStatus(str, enum.Enum):
    REPORTED = "REPORTED"
    AI_ANALYZED = "AI_ANALYZED"
    UNDER_REVIEW = "UNDER_REVIEW"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

class SeverityLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class Issue(Base):
    __tablename__ = "issues"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    issue_type = Column(SQLEnum(IssueType), nullable=False, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    address = Column(String(255), nullable=True)
    ai_confidence = Column(Float, default=0.0)
    severity = Column(SQLEnum(SeverityLevel), default=SeverityLevel.MEDIUM, nullable=False)
    priority_score = Column(Float, default=0.0, index=True)
    status = Column(SQLEnum(IssueStatus), default=IssueStatus.REPORTED, nullable=False, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)
    assigned_officer_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    assigned_at = Column(DateTime, nullable=True)
    progress_percentage = Column(Integer, default=0, nullable=False)
    latest_update = Column(Text, nullable=True)
    estimated_completion_date = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Multi-defect, provenance & verification fields
    detected_defects_json = Column(Text, nullable=True)  # JSON list of all detected defects
    model_provenance_json = Column(Text, nullable=True)  # JSON metadata: models invoked, version, execution time
    verified_category = Column(String(100), nullable=True)  # Officer/Admin verified defect category
    ai_analysis_status = Column(String(50), default="NOT_RUN", nullable=True)  # SUCCESS, NO_DETECTION, VISION_UNAVAILABLE, UNSUPPORTED

    # Relationships
    reporter = relationship("User", foreign_keys=[reporter_id], back_populates="issues")
    assigned_officer = relationship("User", foreign_keys=[assigned_officer_id])
    department = relationship("Department", back_populates="issues")
    images = relationship("IssueImage", back_populates="issue", cascade="all, delete-orphan")
    status_history = relationship("IssueStatusHistory", back_populates="issue", cascade="all, delete-orphan")
    duplicate_relations = relationship("DuplicateIssueRelation", foreign_keys="[DuplicateIssueRelation.original_issue_id]", back_populates="original_issue", cascade="all, delete-orphan")
