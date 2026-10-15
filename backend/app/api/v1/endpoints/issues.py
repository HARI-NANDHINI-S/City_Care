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
from app.models.clarification import IssueClarification
from app.schemas.issue import *
from app.services.ai_service import analyze_issue_image

router=APIRouter()

def q_issue(db, issue_id):
    issue=db.query(Issue).options(
        joinedload(Issue.images),
        joinedload(Issue.department),
        joinedload(Issue.assigned_officer),
        joinedload(Issue.reporter),
        joinedload(Issue.status_history).joinedload(IssueStatusHistory.changed_by),
        joinedload(Issue.clarifications).joinedload(IssueClarification.requested_by)
    ).filter(Issue.id==issue_id).first()
    if not issue: raise HTTPException(404,'Issue not found')
    return issue

def assert_owner_or_authorized(issue,current):
    if current.role==UserRole.CITIZEN and issue.reporter_id!=current.id: raise HTTPException(403,'Not authorized to access this report')
    if current.role==UserRole.OFFICER and issue.department_id and issue.department_id!=current.department_id: raise HTTPException(403,'Issue is outside your department')

def assert_department_access(issue,current):
    if current.role not in (UserRole.ADMIN,UserRole.OFFICER): raise HTTPException(403,'Department authorization required')
    if current.role==UserRole.OFFICER and (not current.department_id or issue.department_id!=current.department_id): raise HTTPException(403,'Issue is outside your department')

def history(db,issue,user,new_status,note=None,progress=None):
    old=issue.status; issue.status=new_status
    db.add(IssueStatusHistory(issue_id=issue.id,previous_status=old,new_status=new_status,changed_by_user_id=user.id,notes=note,progress_percentage=progress))

@router.get('/categories')
def list_categories():
    from app.core.defect_registry import get_active_categories, FUTURE_EXTENSION_REGISTRY, READINESS_LABELS
    return {
        "active_categories": get_active_categories(),
        "total_active": len(get_active_categories()),
        "readiness_labels": READINESS_LABELS,
        "future_extensions": [
            {
                "domain": k.value if hasattr(k, "value") else str(k),
                "title": v.get("title"),
                "scope": v.get("scope"),
                "intended_categories": v.get("intended_categories"),
                "status": "FUTURE_SCOPE"
            }
            for k, v in FUTURE_EXTENSION_REGISTRY.items()
        ]
    }

@router.post('/analyze-image')
def analyze_image(file:UploadFile=File(...), current_user:User=Depends(get_current_user)):
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
    ext = os.path.splitext(file.filename or '')[1].lower() or '.jpg'
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid image format. Allowed: JPG, PNG, WEBP")
    
    name = f'{uuid.uuid4().hex}{ext}'
    path = os.path.join(settings.ORIGINAL_IMG_DIR, name)
    os.makedirs(settings.ORIGINAL_IMG_DIR, exist_ok=True)
    os.makedirs(settings.ANNOTATED_IMG_DIR, exist_ok=True)
    
    max_bytes = settings.MAX_UPLOAD_SIZE_BYTES
    bytes_written = 0
    chunk_size = 64 * 1024  # 64 KiB chunks
    
    try:
        with open(path, 'wb') as f:
            while True:
                chunk = file.file.read(chunk_size)
                if not chunk:
                    break
                bytes_written += len(chunk)
                if bytes_written > max_bytes:
                    f.close()
                    if os.path.exists(path):
                        os.remove(path)
                    max_mb = max_bytes // (1024 * 1024)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Uploaded file exceeds maximum allowed size of {max_mb}MB"
                    )
                f.write(chunk)
    except HTTPException:
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass
        raise
    except Exception as e:
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process image upload: {str(e)}"
        )
    finally:
        try:
            file.file.close()
        except Exception:
            pass
    
    result = analyze_issue_image(path)
    result['original_image_url'] = f'/uploads/original/{name}'
    ann = result.get('annotated_image_filename')
    result['annotated_image_url'] = f'/uploads/annotated/{ann}' if ann else None
    
    if result.get("error"):
        result['status'] = 'vision_unavailable'
        result['message'] = result.get('reason') or result.get('error')
    return result

@router.post('',response_model=IssueDetailOut)
def create_issue(payload:CreateIssueSchema,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    if current_user.role not in (UserRole.CITIZEN,UserRole.ADMIN): raise HTTPException(403,'Only citizens can submit reports')
    
    # Auto-resolve recommended department if available
    from app.services.routing_service import get_recommended_department_code
    target_code = get_recommended_department_code(payload.issue_type.value)
    dept = db.query(Department).filter(Department.code == target_code).first()

    # Determine analysis status & initial workflow status
    is_ai_detected = (payload.ai_confidence or 0) > 0 and (
        bool(payload.bounding_box_json and payload.bounding_box_json != "[]")
        or payload.ai_analysis_status == "SUCCESS"
    )
    initial_status = IssueStatus.AI_ANALYZED if is_ai_detected else IssueStatus.REPORTED
    initial_note = 'AI analysis completed and report submitted.' if is_ai_detected else 'Report submitted with citizen-selected category.'

    issue=Issue(
        title=payload.title,
        description=payload.description,
        issue_type=payload.issue_type,
        latitude=payload.latitude,
        longitude=payload.longitude,
        address=payload.address,
        ai_confidence=payload.ai_confidence,
        severity=payload.severity,
        priority_score=payload.priority_score,
        status=initial_status,
        reporter_id=current_user.id,
        department_id=dept.id if dept else None,
        progress_percentage=0,
        latest_update=initial_note,
        detected_defects_json=payload.detected_defects_json,
        model_provenance_json=payload.model_provenance_json,
        ai_analysis_status=payload.ai_analysis_status or ("SUCCESS" if is_ai_detected else "MANUAL_OR_UNAVAILABLE")
    )
    db.add(issue); db.flush()
    db.add(IssueImage(issue_id=issue.id,original_image_path=payload.original_image_url,annotated_image_path=payload.annotated_image_url,bounding_box_json=payload.bounding_box_json))
    db.add(IssueStatusHistory(issue_id=issue.id,previous_status=None,new_status=IssueStatus.REPORTED,changed_by_user_id=current_user.id,notes='Report submitted.',progress_percentage=0))
    if is_ai_detected:
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

@router.get('', response_model=List[IssueDetailOut])
def list_issues(
    status_filter: Optional[IssueStatus] = None,
    type_filter: Optional[IssueType] = None,
    dept_id: Optional[int] = None,
    min_priority: Optional[float] = None,
    search: Optional[str] = None,
    sort: str = 'newest',
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(Issue).options(
        joinedload(Issue.images),
        joinedload(Issue.department),
        joinedload(Issue.assigned_officer),
        joinedload(Issue.reporter),
        joinedload(Issue.status_history).joinedload(IssueStatusHistory.changed_by)
    )
    if current_user.role == UserRole.OFFICER and current_user.department_id:
        q = q.filter(Issue.department_id == current_user.department_id)
    elif dept_id:
        q = q.filter(Issue.department_id == dept_id)
    if status_filter:
        q = q.filter(Issue.status == status_filter)
    if type_filter:
        q = q.filter(Issue.issue_type == type_filter)
    if min_priority is not None:
        q = q.filter(Issue.priority_score >= min_priority)
    if search:
        s = f"%{search}%"
        q = q.filter(Issue.title.ilike(s) | Issue.address.ilike(s) | Issue.description.ilike(s))
    if sort == 'priority':
        q = q.order_by(Issue.priority_score.desc())
    elif sort == 'oldest':
        q = q.order_by(Issue.created_at.asc())
    else:
        q = q.order_by(Issue.created_at.desc())
    return q.offset(skip).limit(min(limit, 200)).all()

@router.get('/map-data')
def map_data(db:Session=Depends(get_db)):
    issues=db.query(Issue).options(joinedload(Issue.images),joinedload(Issue.department)).all()
    return [{'id':i.id,'title':i.title,'issue_type':i.issue_type.value,'latitude':i.latitude,'longitude':i.longitude,'address':i.address,'status':i.status.value,'severity':i.severity.value,'priority_score':i.priority_score,'department':i.department.name if i.department else None,'image_url':i.images[0].original_image_path if i.images else None,'created_at':i.created_at} for i in issues]

@router.get('/clarifications/pending', response_model=List[IssueDetailOut])
def pending_clarifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Returns issues reported by or assigned to current user that require citizen clarification."""
    q = db.query(Issue).options(
        joinedload(Issue.images),
        joinedload(Issue.department),
        joinedload(Issue.assigned_officer),
        joinedload(Issue.reporter),
        joinedload(Issue.status_history).joinedload(IssueStatusHistory.changed_by),
        joinedload(Issue.clarifications).joinedload(IssueClarification.requested_by)
    )
    if current_user.role == UserRole.CITIZEN:
        q = q.filter(Issue.reporter_id == current_user.id)
    elif current_user.role == UserRole.OFFICER and current_user.department_id:
        q = q.filter(Issue.department_id == current_user.department_id)
    
    issues = q.all()
    return [i for i in issues if i.has_pending_clarification]

@router.get('/{issue_id}',response_model=IssueDetailOut)
def details(issue_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    issue = q_issue(db, issue_id)
    assert_owner_or_authorized(issue, current_user)
    return issue

@router.get('/{issue_id}/timeline',response_model=List[IssueStatusHistoryOut])
def timeline(issue_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    issue = q_issue(db, issue_id)
    assert_owner_or_authorized(issue, current_user)
    return db.query(IssueStatusHistory).filter_by(issue_id=issue_id).order_by(IssueStatusHistory.created_at.asc()).all()


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

@router.patch('/{issue_id}/assign',response_model=IssueDetailOut)
def reassign_department(issue_id:int,payload:AssignDepartmentSchema,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN: raise HTTPException(403,'Only admins can reassign issue departments')
    issue=q_issue(db,issue_id)
    dept=db.query(Department).filter(Department.id==payload.department_id).first()
    if not dept: raise HTTPException(404,'Department not found')
    issue.department_id=dept.id
    note_text = payload.notes or f'Reassigned to {dept.name}'
    issue.latest_update=note_text
    db.add(IssueStatusHistory(issue_id=issue.id,previous_status=issue.status,new_status=issue.status,changed_by_user_id=current_user.id,notes=note_text,progress_percentage=issue.progress_percentage))
    db.commit(); return q_issue(db,issue.id)


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

@router.patch('/{issue_id}/verify-category', response_model=IssueDetailOut)
def verify_category(issue_id: int, payload: VerifyCategorySchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role not in (UserRole.ADMIN, UserRole.OFFICER):
        raise HTTPException(403, 'Only municipal officers or admins can verify and correct defect categories')
    issue = q_issue(db, issue_id)
    assert_department_access(issue, current_user)
    
    reviewer_name = current_user.full_name or f"User #{current_user.id}"
    advances_to_review = issue.status in (IssueStatus.AI_ANALYZED, IssueStatus.REPORTED)
    target_status = IssueStatus.UNDER_REVIEW if advances_to_review else issue.status

    if payload.verified_category == "REJECTED_AS_FALSE_POSITIVE":
        note = f"AI suggestion REJECTED as false positive by reviewer ({reviewer_name}): {payload.notes or 'Rejected during triage'}. Citizen complaint preserved for manual review."
        if issue.verified_category == "REJECTED_AS_FALSE_POSITIVE" and issue.status == target_status and (not payload.notes or issue.latest_update == note):
            return q_issue(db, issue.id)
        issue.verified_category = "REJECTED_AS_FALSE_POSITIVE"
        issue.ai_analysis_status = "AI_SUGGESTION_REJECTED"
        issue.latest_update = note
        history(db, issue, current_user, target_status, note, issue.progress_percentage)
        db.commit()
        return q_issue(db, issue.id)

    from app.core.defect_registry import DEFECT_REGISTRY
    if payload.verified_category not in DEFECT_REGISTRY:
        raise HTTPException(400, f"Invalid category '{payload.verified_category}'. Must be a recognized defect category.")

    old_cat = issue.verified_category or (issue.issue_type.value if hasattr(issue.issue_type, 'value') else str(issue.issue_type))
    note = f"Category reviewed and updated: from '{old_cat}' to '{payload.verified_category}'. {payload.notes or ''}".strip()
    if issue.verified_category == payload.verified_category and issue.status == target_status and (not payload.notes or issue.latest_update == note):
        return q_issue(db, issue.id)

    issue.verified_category = payload.verified_category
    if issue.ai_analysis_status == "AI_SUGGESTION_REJECTED":
        issue.ai_analysis_status = "SUCCESS"
    issue.latest_update = note
    history(db, issue, current_user, target_status, note, issue.progress_percentage)
    db.commit()
    return q_issue(db, issue.id)

@router.post('/{issue_id}/triage', response_model=IssueDetailOut)
def triage_issue(
    issue_id: int,
    payload: TriageReviewSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Phase 4 Human Verification and Safe Triage:
    Auditable workflow where AI predictions remain suggestions until an authorized
    municipal reviewer (Admin or Department Officer) records a triage decision.
    
    Supported Outcomes:
    - CONFIRM: Validates that the AI-suggested defect matches reality.
    - CORRECT: Reclassifies defect to a different valid category while preserving original AI/citizen data.
    - REJECT_SUGGESTION: Rejects the AI prediction as false positive/invalid without deleting the citizen report.
    - REQUEST_INFO: Requests additional evidence/clarification from citizen while keeping report under review.
    """
    issue = q_issue(db, issue_id)
    assert_department_access(issue, current_user)

    from app.core.defect_registry import DEFECT_REGISTRY

    advances_to_review = issue.status in (IssueStatus.AI_ANALYZED, IssueStatus.REPORTED)
    target_status = IssueStatus.UNDER_REVIEW if advances_to_review else issue.status
    reviewer_name = current_user.full_name or f"User #{current_user.id}"

    is_duplicate = False

    if payload.decision == ReviewDecision.CONFIRM:
        confirmed_cat = payload.verified_category or (issue.issue_type.value if hasattr(issue.issue_type, 'value') else str(issue.issue_type))
        if confirmed_cat not in DEFECT_REGISTRY:
            raise HTTPException(400, f"Cannot confirm invalid category '{confirmed_cat}'. Must be a recognized defect category.")
        
        note = f"AI suggestion CONFIRMED by reviewer ({reviewer_name}): '{confirmed_cat}'. {payload.notes or ''}".strip()
        if issue.verified_category == confirmed_cat and issue.status == target_status and (not payload.notes or issue.latest_update == note):
            is_duplicate = True
        else:
            issue.verified_category = confirmed_cat
            if issue.ai_analysis_status == "AI_SUGGESTION_REJECTED":
                issue.ai_analysis_status = "SUCCESS"
            issue.latest_update = note
            history(db, issue, current_user, target_status, note, issue.progress_percentage)

    elif payload.decision == ReviewDecision.CORRECT:
        if not payload.verified_category:
            raise HTTPException(400, "verified_category is required when correcting/reclassifying a defect.")
        if payload.verified_category not in DEFECT_REGISTRY:
            raise HTTPException(400, f"Cannot reclassify to invalid category '{payload.verified_category}'.")
        
        orig_cat = issue.issue_type.value if hasattr(issue.issue_type, 'value') else str(issue.issue_type)
        note = f"AI suggestion CORRECTED by reviewer ({reviewer_name}): reclassified from '{orig_cat}' to '{payload.verified_category}'. {payload.notes or ''}".strip()
        if issue.verified_category == payload.verified_category and issue.status == target_status and (not payload.notes or issue.latest_update == note):
            is_duplicate = True
        else:
            issue.verified_category = payload.verified_category
            if issue.ai_analysis_status == "AI_SUGGESTION_REJECTED":
                issue.ai_analysis_status = "SUCCESS"
            # Note: issue.issue_type and detected_defects_json are preserved intact!
            issue.latest_update = note
            history(db, issue, current_user, target_status, note, issue.progress_percentage)

    elif payload.decision == ReviewDecision.REJECT_SUGGESTION:
        if not payload.notes or len(payload.notes.strip()) < 3:
            raise HTTPException(400, "A reason/note is required when rejecting an AI suggestion.")
        
        note = f"AI suggestion REJECTED as false positive by reviewer ({reviewer_name}): {payload.notes.strip()}. Citizen complaint preserved for manual review."
        if issue.verified_category == "REJECTED_AS_FALSE_POSITIVE" and issue.status == target_status and issue.latest_update == note:
            is_duplicate = True
        else:
            issue.verified_category = "REJECTED_AS_FALSE_POSITIVE"
            issue.ai_analysis_status = "AI_SUGGESTION_REJECTED"
            # Safety constraint: Do NOT delete report or erase citizen complaint; keep under review for manual handling
            issue.latest_update = note
            history(db, issue, current_user, target_status, note, issue.progress_percentage)

    elif payload.decision == ReviewDecision.REQUEST_INFO:
        if not payload.notes or len(payload.notes.strip()) < 3:
            raise HTTPException(400, "Please specify what additional information is needed from the citizen.")
        
        note = f"Additional information requested by reviewer ({reviewer_name}): {payload.notes.strip()}"
        if issue.latest_update == note and issue.status == target_status:
            is_duplicate = True
        else:
            issue.latest_update = note
            history(db, issue, current_user, target_status, note, issue.progress_percentage)
            clarification = IssueClarification(
                issue_id=issue.id,
                request_text=payload.notes.strip(),
                requested_by_user_id=current_user.id,
                status="PENDING"
            )
            db.add(clarification)

    else:
        raise HTTPException(400, f"Unsupported triage decision '{payload.decision}'.")

    if not is_duplicate:
        db.commit()
    return q_issue(db, issue.id)


@router.get('/{issue_id}/clarifications', response_model=List[IssueClarificationOut])
def list_clarifications(issue_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    issue = q_issue(db, issue_id)
    assert_owner_or_authorized(issue, current_user)
    return db.query(IssueClarification).options(joinedload(IssueClarification.requested_by)).filter_by(issue_id=issue.id).order_by(IssueClarification.created_at.asc()).all()


@router.post('/{issue_id}/clarifications', response_model=IssueClarificationOut)
def create_clarification_request(issue_id: int, payload: RequestClarificationSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    issue = q_issue(db, issue_id)
    assert_department_access(issue, current_user)
    
    reviewer_name = current_user.full_name or f"User #{current_user.id}"
    note = f"Additional information requested by reviewer ({reviewer_name}): {payload.notes.strip()}"
    advances_to_review = issue.status in (IssueStatus.AI_ANALYZED, IssueStatus.REPORTED)
    target_status = IssueStatus.UNDER_REVIEW if advances_to_review else issue.status
    
    issue.latest_update = note
    history(db, issue, current_user, target_status, note, issue.progress_percentage)
    
    clarification = IssueClarification(
        issue_id=issue.id,
        request_text=payload.notes.strip(),
        requested_by_user_id=current_user.id,
        status="PENDING"
    )
    db.add(clarification)
    db.commit()
    db.refresh(clarification)
    return clarification


@router.post('/{issue_id}/clarifications/{clarification_id}/respond', response_model=IssueDetailOut)
def respond_to_clarification(
    issue_id: int,
    clarification_id: int,
    payload: CitizenClarificationResponseSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    issue = q_issue(db, issue_id)
    if current_user.role != UserRole.CITIZEN or issue.reporter_id != current_user.id:
        raise HTTPException(403, "Only the citizen who submitted this report can respond to clarification requests")
    
    clarification = db.query(IssueClarification).filter_by(id=clarification_id, issue_id=issue.id).first()
    if not clarification:
        raise HTTPException(404, "Clarification request not found")
    
    clarification.response_text = payload.response_text.strip()
    clarification.response_image_path = payload.supplementary_image_url
    clarification.responded_at = datetime.utcnow()
    clarification.status = "RESPONDED"
    
    if payload.supplementary_image_url:
        db.add(IssueImage(issue_id=issue.id, original_image_path=payload.supplementary_image_url))
    
    note = f"Citizen clarification response: {payload.response_text.strip()}"
    issue.latest_update = note
    
    # Safety constraint: Citizen response does NOT mark report verified or resolved
    history(db, issue, current_user, issue.status, note, issue.progress_percentage)
    db.commit()
    return q_issue(db, issue.id)


