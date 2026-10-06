from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base

class IssueType(str, enum.Enum):
    POTHOLE = "Pothole"; GARBAGE = "Garbage Accumulation"; WATERLOGGING = "Waterlogging"; STREETLIGHT = "Broken Streetlight"; MANHOLE = "Open Manhole"; ROAD_DAMAGE = "Road Damage"
class IssueStatus(str, enum.Enum):
    REPORTED="REPORTED"; AI_ANALYZED="AI_ANALYZED"; UNDER_REVIEW="UNDER_REVIEW"; ASSIGNED="ASSIGNED"; IN_PROGRESS="IN_PROGRESS"; RESOLVED="RESOLVED"; CLOSED="CLOSED"
class SeverityLevel(str, enum.Enum):
    LOW="LOW"; MEDIUM="MEDIUM"; HIGH="HIGH"; CRITICAL="CRITICAL"

class Issue(Base):
    __tablename__="issues"
    id=Column(Integer, primary_key=True, index=True)
    title=Column(String(200), nullable=False); description=Column(Text, nullable=True)
    issue_type=Column(SQLEnum(IssueType), nullable=False, index=True)
    latitude=Column(Float, nullable=False, index=True); longitude=Column(Float, nullable=False, index=True); address=Column(String(255), nullable=True)
    ai_confidence=Column(Float, default=0.0); severity=Column(SQLEnum(SeverityLevel), default=SeverityLevel.MEDIUM, nullable=False); priority_score=Column(Float, default=0.0, index=True)
    status=Column(SQLEnum(IssueStatus), default=IssueStatus.REPORTED, nullable=False, index=True)
    reporter_id=Column(Integer, ForeignKey("users.id"), nullable=False, index=True); department_id=Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)
    assigned_officer_id=Column(Integer, ForeignKey("users.id"), nullable=True, index=True); assigned_at=Column(DateTime, nullable=True)
    progress_percentage=Column(Integer, default=0, nullable=False); latest_update=Column(Text, nullable=True); estimated_completion_date=Column(DateTime, nullable=True); resolved_at=Column(DateTime, nullable=True); closed_at=Column(DateTime, nullable=True)
    created_at=Column(DateTime, default=datetime.utcnow); updated_at=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reporter=relationship("User", foreign_keys=[reporter_id], back_populates="issues")
    assigned_officer=relationship("User", foreign_keys=[assigned_officer_id])
    department=relationship("Department", back_populates="issues"); images=relationship("IssueImage", back_populates="issue", cascade="all, delete-orphan"); status_history=relationship("IssueStatusHistory", back_populates="issue", cascade="all, delete-orphan")
    duplicate_relations=relationship("DuplicateIssueRelation", foreign_keys="[DuplicateIssueRelation.original_issue_id]", back_populates="original_issue", cascade="all, delete-orphan")
