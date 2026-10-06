from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class DuplicateIssueRelation(Base):
    __tablename__ = "duplicate_issue_relations"

    id = Column(Integer, primary_key=True, index=True)
    original_issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False, index=True)
    duplicate_issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False, index=True)
    distance_meters = Column(Float, nullable=False)
    similarity_score = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    original_issue = relationship("Issue", foreign_keys=[original_issue_id], back_populates="duplicate_relations")
    duplicate_issue = relationship("Issue", foreign_keys=[duplicate_issue_id])
