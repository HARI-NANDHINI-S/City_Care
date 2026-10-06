from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class IssueImage(Base):
    __tablename__ = "issue_images"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False, index=True)
    original_image_path = Column(String(255), nullable=False)
    annotated_image_path = Column(String(255), nullable=True)
    bounding_box_json = Column(Text, nullable=True)  # JSON string of bounding boxes
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    issue = relationship("Issue", back_populates="images")
