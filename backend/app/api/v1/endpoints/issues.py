import json, os, uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user, require_role
from app.core.config import settings
from app.models.user import User, UserRole
from app.models.issue import Issue, IssueStatus, IssueType, SeverityLevel
from app.models.department import Department
from app.models.image import IssueImage
from app.models.history import IssueStatusHistory
from app.schemas.issue import *
from app.services.ai_service import analyze_issue_image

router=APIRouter()

def q_issue(db, issue_id):
    issue=db.query(Issue).options(joinedload(Issue.images),joinedload(Issue.department),joinedload(Issue.assigned_officer),joinedload(Issue.reporter),joinedload(Issue.status_history).joinedload(IssueStatusHistory.changed_by)).filter(Issue.id==issue_id).first()
    if not issue: raise HTTPException(404,'Issue not found')
    return issue

def assert_owner_or_authorized(issue,current):
    if current.role==UserRole.CITIZEN and issue.reporter_id!=current.id: raise HTTPException(403,'Not authorized to access this report')
    if current.role==UserRole.OFFICER and issue.department_id!=current.department_id: raise HTTPException(403,'Issue is outside your department')

def assert_department_access(issue,current):
    if current.role not in (UserRole.ADMIN,UserRole.OFFICER): raise HTTPException(403,'Department authorization required')
    if current.role==UserRole.OFFICER and (not current.department_id or issue.department_id!=current.department_id): raise HTTPException(403,'Issue is outside your department')

def history(db,issue,user,new_status,note=None,progress=None):
    old=issue.status; issue.status=new_status
    db.add(IssueStatusHistory(issue_id=issue.id,previous_status=old,new_status=new_status,changed_by_user_id=user.id,notes=note,progress_percentage=progress))

@router.post('/analyze-image')
def analyze_image(file:UploadFile=File(...), current_user:User=Depends(get_current_user)):
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
    ext=os.path.splitext(file.filename or '')[1].lower() or '.jpg'
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid image format. Allowed: JPG, PNG, WEBP")
    
    name=f'{uuid.uuid4().hex}{ext}'
    path=os.path.join(settings.ORIGINAL_IMG_DIR,name)
    os.makedirs(settings.ORIGINAL_IMG_DIR,exist_ok=True)
    os.makedirs(settings.ANNOTATED_IMG_DIR,exist_ok=True)
    
    with open(path,'wb') as f: f.write(file.file.read())
    result=analyze_issue_image(path)
    if result.get("error"):
        raise HTTPException(status_code=503, detail=result["error"])
    result['original_image_url']=f'/uploads/original/{name}'
    ann=result.get('annotated_image_filename')
    result['annotated_image_url']=f'/uploads/annotated/{ann}' if ann else None
    return result

@router.post('',response_model=IssueDetailOut)
def create_issue(payload:CreateIssueSchema,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    if current_user.role not in (UserRole.CITIZEN,UserRole.ADMIN): raise HTTPException(403,'Only citizens can submit reports')
    dept=None
    # route by department code/name already supplied by AI category
    from app.services.routing_service import get_recommended_department_code
    dept=db.query(Department).filter(Department.code==get_recommended_department_code(payload.issue_type.value)).first()
    issue=Issue(title=payload.title,description=payload.description,issue_type=payload.issue_type,latitude=payload.latitude,longitude=payload.longitude,address=payload.address,ai_confidence=payload.ai_confidence,severity=payload.severity,priority_score=payload.priority_score,status=IssueStatus.AI_ANALYZED,reporter_id=current_user.id,department_id=dept.id if dept else None,progress_percentage=0,latest_update='AI analysis completed and report submitted.')
    db.add(issue); db.flush()
    db.add(IssueImage(issue_id=issue.id,original_image_path=payload.original_image_url,annotated_image_path=payload.annotated_image_url,bounding_box_json=payload.bounding_box_json))
    db.add(IssueStatusHistory(issue_id=issue.id,previous_status=None,new_status=IssueStatus.REPORTED,changed_by_user_id=current_user.id,notes='Report submitted.',progress_percentage=0))
    db.add(IssueStatusHistory(issue_id=issue.id,previous_status=IssueStatus.REPORTED,new_status=IssueStatus.AI_ANALYZED,changed_by_user_id=current_user.id,notes='AI analysis completed.',progress_percentage=0))
    db.commit(); return q_issue(db,issue.id)

@router.get('/stats/citizen',response_model=DashboardStats)
def citizen_stats(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    q=db.query(Issue).filter(Issue.reporter_id==current_user.id)
    return DashboardStats(total_issues=q.count(),under_review=q.filter(Issue.status==IssueStatus.UNDER_REVIEW).count(),assigned=q.filter(Issue.status==IssueStatus.ASSIGNED).count(),in_progress=q.filter(Issue.status==IssueStatus.IN_PROGRESS).count(),resolved=q.filter(Issue.status.in_([IssueStatus.RESOLVED,IssueStatus.CLOSED])).count(),high_priority=q.filter(Issue.severity.in_([SeverityLevel.HIGH,SeverityLevel.CRITICAL])).count())

@router.get('/my-reports',response_model=List[IssueDetailOut])
def my_reports(status_filter:Optional[IssueStatus]=None,category:Optional[IssueType]=None,severity:Optional[SeverityLevel]=None,search:Optional[str]=None,sort:str='newest',skip:int=0,limit:int=50,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    q=db.query(Issue).filter(Issue.reporter_id==current_user.id)
    if status_filter:q=q.filter(Issue.status==status_filter)
    if category:q=q.filter(Issue.issue_type==category)
    if severity:q=q.filter(Issue.severity==severity)
    if search:q=q.filter(Issue.title.ilike(f'%{search}%'))
    q=q.order_by(Issue.created_at.asc() if sort=='oldest' else Issue.created_at.desc())
    return q.offset(skip).limit(min(limit,100)).all()

@router.get('/department/assigned',response_model=List[IssueDetailOut])
def department_issues(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    if current_user.role not in (UserRole.ADMIN,UserRole.OFFICER): raise HTTPException(403,'Department authorization required')
    q=db.query(Issue)
    if current_user.role==UserRole.OFFICER:
        if not current_user.department_id: raise HTTPException(400,'Officer has no department')
        q=q.filter(Issue.department_id==current_user.department_id)
    return q.order_by(Issue.created_at.desc()).all()

@router.get('/map-data')
def map_data(db:Session=Depends(get_db)):
    issues=db.query(Issue).options(joinedload(Issue.images),joinedload(Issue.department)).all()
    return [{'id':i.id,'title':i.title,'issue_type':i.issue_type.value,'latitude':i.latitude,'longitude':i.longitude,'address':i.address,'status':i.status.value,'severity':i.severity.value,'priority_score':i.priority_score,'department':i.department.name if i.department else None,'image_url':i.images[0].original_image_path if i.images else None,'created_at':i.created_at} for i in issues]

@router.get('/{issue_id}',response_model=IssueDetailOut)
def details(issue_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    issue=q_issue(db,issue_id); assert_owner_or_authorized(issue,current_user); return issue

@router.get('/{issue_id}/timeline',response_model=List[IssueStatusHistoryOut])
def timeline(issue_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    issue=q_issue(db,issue_id); assert_owner_or_authorized(issue,current_user); return db.query(IssueStatusHistory).filter_by(issue_id=issue_id).order_by(IssueStatusHistory.created_at.asc()).all()

@router.post('/{issue_id}/accept',response_model=IssueDetailOut)
def accept(issue_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    issue=q_issue(db,issue_id); assert_department_access(issue,current_user); history(db,issue,current_user,IssueStatus.UNDER_REVIEW,'Issue accepted by department for review.',issue.progress_percentage); db.commit(); return q_issue(db,issue.id)

@router.post('/{issue_id}/reject',response_model=IssueDetailOut)
def reject(issue_id:int,payload:RejectIssueSchema,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    issue=q_issue(db,issue_id); assert_department_access(issue,current_user); history(db,issue,current_user,IssueStatus.CLOSED,f'Rejected: {payload.reason}',issue.progress_percentage); issue.latest_update=f'Rejected: {payload.reason}'; issue.closed_at=datetime.utcnow(); db.commit(); return q_issue(db,issue.id)

@router.post('/{issue_id}/assign',response_model=IssueDetailOut)
def assign_officer(issue_id:int,payload:AssignOfficerSchema,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    issue=q_issue(db,issue_id); assert_department_access(issue,current_user); officer=db.query(User).filter(User.id==payload.officer_id,User.role==UserRole.OFFICER).first()
    if not officer: raise HTTPException(404,'Officer not found')
    if issue.department_id and officer.department_id!=issue.department_id: raise HTTPException(400,'Officer belongs to another department')
    issue.assigned_officer_id=officer.id; issue.assigned_at=datetime.utcnow(); history(db,issue,current_user,IssueStatus.ASSIGNED,f'Officer assigned: {officer.full_name}',issue.progress_percentage); db.commit(); return q_issue(db,issue.id)

@router.patch('/{issue_id}/status',response_model=IssueDetailOut)
def update_status(issue_id:int,payload:StatusUpdateSchema,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    issue=q_issue(db,issue_id); assert_department_access(issue,current_user); history(db,issue,current_user,payload.status,payload.notes,issue.progress_percentage); issue.latest_update=payload.notes or issue.latest_update
    if payload.status==IssueStatus.RESOLVED: issue.progress_percentage=100; issue.resolved_at=datetime.utcnow()
    if payload.status==IssueStatus.CLOSED: issue.closed_at=datetime.utcnow()
    db.commit(); return q_issue(db,issue.id)

@router.patch('/{issue_id}/progress',response_model=IssueDetailOut)
def progress(issue_id:int,payload:UpdateProgressSchema,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    issue=q_issue(db,issue_id); assert_department_access(issue,current_user); issue.progress_percentage=payload.progress_percentage; issue.latest_update=payload.note or issue.latest_update
    target=IssueStatus.IN_PROGRESS if payload.progress_percentage>0 and issue.status not in (IssueStatus.RESOLVED,IssueStatus.CLOSED) else issue.status
    history(db,issue,current_user,target,payload.note or f'Progress updated to {payload.progress_percentage}%',payload.progress_percentage); db.commit(); return q_issue(db,issue.id)

@router.post('/{issue_id}/notes',response_model=IssueDetailOut)
def add_note(issue_id:int,payload:UpdateProgressSchema,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    issue=q_issue(db,issue_id); assert_department_access(issue,current_user)
    if not payload.note: raise HTTPException(400,'A progress note is required')
    issue.latest_update=payload.note; issue.progress_percentage=payload.progress_percentage
    db.add(IssueStatusHistory(issue_id=issue.id,previous_status=issue.status,new_status=issue.status,changed_by_user_id=current_user.id,notes=payload.note,progress_percentage=payload.progress_percentage)); db.commit(); return q_issue(db,issue.id)

@router.patch('/{issue_id}/estimate',response_model=IssueDetailOut)
def estimate(issue_id:int,payload:UpdateEstimateSchema,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    issue=q_issue(db,issue_id); assert_department_access(issue,current_user); issue.estimated_completion_date=payload.estimated_completion_date; db.add(IssueStatusHistory(issue_id=issue.id,previous_status=issue.status,new_status=issue.status,changed_by_user_id=current_user.id,notes=f'Estimated completion date set to {payload.estimated_completion_date.isoformat()}',progress_percentage=issue.progress_percentage)); db.commit(); return q_issue(db,issue.id)

@router.post('/{issue_id}/resolve',response_model=IssueDetailOut)
def resolve(issue_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    issue=q_issue(db,issue_id); assert_department_access(issue,current_user); issue.progress_percentage=100; issue.resolved_at=datetime.utcnow(); issue.latest_update='Issue marked as resolved.'; history(db,issue,current_user,IssueStatus.RESOLVED,issue.latest_update,100); db.commit(); return q_issue(db,issue.id)

@router.post('/{issue_id}/close',response_model=IssueDetailOut)
def close(issue_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    issue=q_issue(db,issue_id); assert_department_access(issue,current_user); issue.closed_at=datetime.utcnow(); history(db,issue,current_user,IssueStatus.CLOSED,'Issue formally closed.',issue.progress_percentage); db.commit(); return q_issue(db,issue.id)
