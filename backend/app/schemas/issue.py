from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import enum
from app.models.issue import IssueStatus, IssueType, SeverityLevel

class ReviewDecision(str, enum.Enum):
    CONFIRM = "CONFIRM"
    CORRECT = "CORRECT"
    REJECT_SUGGESTION = "REJECT_SUGGESTION"
    REQUEST_INFO = "REQUEST_INFO"

class TriageReviewSchema(BaseModel):
    decision: ReviewDecision
    verified_category: Optional[str] = None
    notes: Optional[str] = None

class UserSimple(BaseModel):
    id: int
    full_name: Optional[str] = None
    email: str
    class Config:
        from_attributes = True

class DepartmentSimple(BaseModel):
    id: int
    name: str
    code: Optional[str] = None
    contact_email: Optional[str] = None
    class Config:
        from_attributes = True

class IssueImageOut(BaseModel):
    id: int
    original_image_path: str
    annotated_image_path: Optional[str] = None
    bounding_box_json: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class IssueStatusHistoryOut(BaseModel):
    id: int
    previous_status: Optional[IssueStatus] = None
    new_status: IssueStatus
    notes: Optional[str] = None
    progress_percentage: Optional[int] = None
    created_at: datetime
    changed_by: Optional[UserSimple] = None
    class Config:
        from_attributes = True

class IssueDetailOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    issue_type: IssueType
    ai_confidence: float
    severity: SeverityLevel
    priority_score: float
    status: IssueStatus
    latitude: float
    longitude: float
    address: Optional[str] = None
    progress_percentage: int = 0
    latest_update: Optional[str] = None
    estimated_completion_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    assigned_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    # Extended AI provenance & verification fields
    detected_defects_json: Optional[str] = None
    model_provenance_json: Optional[str] = None
    verified_category: Optional[str] = None
    ai_analysis_status: Optional[str] = None

    # Phase 4 Human Verification & Safe Triage fields
    is_verified: bool = False
    verification_status: Optional[str] = "UNVERIFIED"
    ai_suggested_category: Optional[str] = None

    reporter: Optional[UserSimple] = None
    department: Optional[DepartmentSimple] = None
    assigned_officer: Optional[UserSimple] = None
    images: List[IssueImageOut] = []
    status_history: List[IssueStatusHistoryOut] = []

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_issues: int
    under_review: int
    assigned: int
    in_progress: int
    resolved: int
    high_priority: int

class UpdateProgressSchema(BaseModel):
    progress_percentage: int = Field(ge=0, le=100)
    note: Optional[str] = None

class AssignOfficerSchema(BaseModel):
    officer_id: int

class AssignDepartmentSchema(BaseModel):
    department_id: int
    notes: Optional[str] = None

class RejectIssueSchema(BaseModel):
    reason: str = Field(min_length=3, max_length=2000)

class UpdateEstimateSchema(BaseModel):
    estimated_completion_date: datetime

class StatusUpdateSchema(BaseModel):
    status: IssueStatus
    notes: Optional[str] = None

class VerifyCategorySchema(BaseModel):
    verified_category: str
    notes: Optional[str] = None

class CreateIssueSchema(BaseModel):
    title: str
    description: Optional[str] = None
    issue_type: IssueType
    latitude: float
    longitude: float
    address: Optional[str] = None
    original_image_url: str
    annotated_image_url: Optional[str] = None
    ai_confidence: float = 0
    severity: SeverityLevel = SeverityLevel.MEDIUM
    priority_score: float = 0
    bounding_box_json: Optional[str] = None
    detected_defects_json: Optional[str] = None
    model_provenance_json: Optional[str] = None
    ai_analysis_status: Optional[str] = None
