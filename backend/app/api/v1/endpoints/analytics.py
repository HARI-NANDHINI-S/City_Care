from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.issue import Issue, IssueStatus, SeverityLevel, IssueType
from app.models.department import Department
from app.schemas.analytics import AnalyticsDashboardResponse, DepartmentStat

router = APIRouter()

@router.get("/dashboard", response_model=AnalyticsDashboardResponse)
def get_analytics_dashboard(db: Session = Depends(get_db)):
    all_issues = db.query(Issue).all()
    departments = db.query(Department).all()

    total_issues = len(all_issues)
    open_issues = sum(1 for i in all_issues if i.status in [IssueStatus.REPORTED, IssueStatus.AI_ANALYZED, IssueStatus.UNDER_REVIEW, IssueStatus.ASSIGNED])
    in_progress = sum(1 for i in all_issues if i.status == IssueStatus.IN_PROGRESS)
    resolved = sum(1 for i in all_issues if i.status == IssueStatus.RESOLVED)
    critical_count = sum(1 for i in all_issues if i.severity == SeverityLevel.CRITICAL)

    by_category = {}
    for t in IssueType:
        by_category[t.value] = sum(1 for i in all_issues if i.issue_type == t)

    by_severity = {}
    for s in SeverityLevel:
        by_severity[s.value] = sum(1 for i in all_issues if i.severity == s)

    by_status = {}
    for st in IssueStatus:
        by_status[st.value] = sum(1 for i in all_issues if i.status == st)

    dept_stats = []
    for dept in departments:
        dept_issues = [i for i in all_issues if i.department_id == dept.id]
        total_assigned = len(dept_issues)
        dept_pending = sum(1 for i in dept_issues if i.status in [IssueStatus.REPORTED, IssueStatus.AI_ANALYZED, IssueStatus.UNDER_REVIEW, IssueStatus.ASSIGNED])
        dept_prog = sum(1 for i in dept_issues if i.status == IssueStatus.IN_PROGRESS)
        dept_res = sum(1 for i in dept_issues if i.status == IssueStatus.RESOLVED)
        rate = round((dept_res / total_assigned * 100.0), 1) if total_assigned > 0 else 0.0

        dept_stats.append(DepartmentStat(
            department_id=dept.id,
            department_name=dept.name,
            total_assigned=total_assigned,
            pending=dept_pending,
            in_progress=dept_prog,
            resolved=dept_res,
            resolution_rate=rate
        ))

    return AnalyticsDashboardResponse(
        total_issues=total_issues,
        open_issues=open_issues,
        in_progress_issues=in_progress,
        resolved_issues=resolved,
        critical_issues_count=critical_count,
        issues_by_category=by_category,
        issues_by_severity=by_severity,
        issues_by_status=by_status,
        department_performance=dept_stats
    )
