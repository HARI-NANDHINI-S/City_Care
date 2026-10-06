from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
)

from app.schemas.department import (
    DepartmentCreate,
    DepartmentResponse,
)

from app.schemas.issue import (
    UserSimple,
    DepartmentSimple,
    IssueImageOut,
    IssueStatusHistoryOut,
    IssueDetailOut,
    DashboardStats,
    UpdateProgressSchema,
    AssignOfficerSchema,
    RejectIssueSchema,
    UpdateEstimateSchema,
    StatusUpdateSchema,
    CreateIssueSchema,
)

from app.schemas.analytics import (
    AnalyticsDashboardResponse,
    DepartmentStat,
)

__all__ = [
    # User
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "Token",

    # Department
    "DepartmentCreate",
    "DepartmentResponse",

    # Issue
    "UserSimple",
    "DepartmentSimple",
    "IssueImageOut",
    "IssueStatusHistoryOut",
    "IssueDetailOut",
    "DashboardStats",
    "UpdateProgressSchema",
    "AssignOfficerSchema",
    "RejectIssueSchema",
    "UpdateEstimateSchema",
    "StatusUpdateSchema",
    "CreateIssueSchema",

    # Analytics
    "AnalyticsDashboardResponse",
    "DepartmentStat",
]