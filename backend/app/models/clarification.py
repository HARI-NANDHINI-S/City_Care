from sqlalchemy import Column, Integer, Text, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class IssueClarification(Base):
    __tablename__ = "issue_clarifications"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False, index=True)
    request_text = Column(Text, nullable=False)
    requested_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    response_text = Column(Text, nullable=True)
    response_image_path = Column(String(500), nullable=True)
    responded_at = Column(DateTime, nullable=True)

    # Status: PENDING (awaiting citizen response) | RESPONDED (citizen provided information)
    status = Column(String(50), default="PENDING", nullable=False, index=True)

    # Relationships
    issue = relationship("Issue", back_populates="clarifications")
    requested_by = relationship("User", foreign_keys=[requested_by_user_id])

    @property
    def requested_by_name(self) -> str:
        """Name of the municipal reviewer who requested information."""
        if self.requested_by and getattr(self.requested_by, "full_name", None):
            return self.requested_by.full_name
        return f"Reviewer #{self.requested_by_user_id}"
