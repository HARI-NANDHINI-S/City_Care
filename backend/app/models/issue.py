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
    status_history = relationship("IssueStatusHistory", back_populates="issue", cascade="all, delete-orphan", order_by="IssueStatusHistory.created_at.asc()")
    duplicate_relations = relationship("DuplicateIssueRelation", foreign_keys="[DuplicateIssueRelation.original_issue_id]", back_populates="original_issue", cascade="all, delete-orphan")
    clarifications = relationship("IssueClarification", back_populates="issue", cascade="all, delete-orphan", order_by="IssueClarification.created_at.asc()")

    @property
    def has_pending_clarification(self) -> bool:
        """True if there is an active clarification request awaiting citizen response."""
        if hasattr(self, "clarifications") and self.clarifications:
            return any(c.status == "PENDING" for c in self.clarifications)
        return False

    @property
    def is_verified(self) -> bool:
        """True only if an authorized human reviewer has confirmed or corrected the defect category."""
        return bool(self.verified_category and self.verified_category != "REJECTED_AS_FALSE_POSITIVE")

    @property
    def verification_status(self) -> str:
        """
        Human triage verification state:
        - UNVERIFIED: Prediction remains an unconfirmed suggestion.
        - CONFIRMED: Reviewer validated that the suggested defect matches reality.
        - CORRECTED: Reviewer reclassified the defect to a different active category.
        - REJECTED: Reviewer determined the suggestion is a false positive / invalid.
        """
        if not self.verified_category:
            return "UNVERIFIED"
        if self.verified_category == "REJECTED_AS_FALSE_POSITIVE":
            return "REJECTED"
        expected = self.issue_type.value if hasattr(self.issue_type, 'value') else str(self.issue_type)
        if self.verified_category == expected:
            return "CONFIRMED"
        return "CORRECTED"

    @property
    def ai_suggested_category(self) -> str:
        """Original AI or reported category suggested prior to human verification."""
        if (self.ai_confidence or 0) > 0 or self.ai_analysis_status in ("SUCCESS", "AI_SUGGESTION_REJECTED") or self.detected_defects_json:
            return self.issue_type.value if hasattr(self.issue_type, 'value') else str(self.issue_type)
        return None

    @property
    def last_reviewed_at(self) -> datetime:
        """Timestamp of the most recent human triage or verification decision."""
        if hasattr(self, "status_history") and self.status_history:
            sorted_history = sorted(
                self.status_history,
                key=lambda h: (h.created_at or datetime.min, getattr(h, "id", 0) or 0),
                reverse=True
            )
            for h in sorted_history:
                if h.notes and any(k in h.notes for k in ("CONFIRMED", "CORRECTED", "REJECTED", "verified as", "reviewed and updated", "information requested")):
                    return h.created_at
        if self.verified_category:
            return self.updated_at
        return None

    @property
    def last_reviewed_by_name(self) -> str:
        """Full name of the reviewer who recorded the most recent triage decision."""
        if hasattr(self, "status_history") and self.status_history:
            sorted_history = sorted(
                self.status_history,
                key=lambda h: (h.created_at or datetime.min, getattr(h, "id", 0) or 0),
                reverse=True
            )
            for h in sorted_history:
                if h.notes and any(k in h.notes for k in ("CONFIRMED", "CORRECTED", "REJECTED", "verified as", "reviewed and updated", "information requested")):
                    if h.changed_by and getattr(h.changed_by, "full_name", None):
                        return h.changed_by.full_name
                    import re
                    match = re.search(r"reviewer \(([^)]+)\)", h.notes)
                    if match:
                        return match.group(1)
                    if getattr(h, "changed_by_user_id", None):
                        return f"User #{h.changed_by_user_id}"
                    return None
        return None

