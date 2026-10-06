from sqlalchemy import Column,Integer,Text,DateTime,ForeignKey,Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
from app.models.issue import IssueStatus
class IssueStatusHistory(Base):
    __tablename__='issue_status_history'
    id=Column(Integer,primary_key=True,index=True); issue_id=Column(Integer,ForeignKey('issues.id'),nullable=False,index=True)
    previous_status=Column(SQLEnum(IssueStatus),nullable=True); new_status=Column(SQLEnum(IssueStatus),nullable=False)
    changed_by_user_id=Column(Integer,ForeignKey('users.id'),nullable=False); notes=Column(Text,nullable=True); progress_percentage=Column(Integer,nullable=True); created_at=Column(DateTime,default=datetime.utcnow)
    issue=relationship('Issue',back_populates='status_history'); changed_by=relationship('User',back_populates='status_changes')
