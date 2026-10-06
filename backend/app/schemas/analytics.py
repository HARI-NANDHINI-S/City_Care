from pydantic import BaseModel
from typing import Dict, List

class DepartmentStat(BaseModel):
    department_id: int
    department_name: str
    total_assigned: int
    pending: int
    in_progress: int
    resolved: int
    resolution_rate: float

class AnalyticsDashboardResponse(BaseModel):
    total_issues: int
    open_issues: int
    in_progress_issues: int
    resolved_issues: int
    critical_issues_count: int
    issues_by_category: Dict[str, int]
    issues_by_severity: Dict[str, int]
    issues_by_status: Dict[str, int]
    department_performance: List[DepartmentStat]
