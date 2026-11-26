from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.authentication.security import require_roles, current_user, faculty_profile_of
from app.models import *
from app.schemas.schemas import *
from app.services.access import to_dict, dept_scope
from app.services.data_loader import notify

router = APIRouter(tags=["workflow"])
ADMIN = require_roles("admin"); STAFF = require_roles("admin", "hod"); FAC = require_roles("faculty")

# ---------------------------------------------------------------- approvals
@router.post("/approvals/submit", status_code=201)
def submit(body: SubmitIn, user: User = Depends(ADMIN), db: Session = Depends(get_db)):
    v = db.get(TimetableVersion, body.version_id)
    if not v: raise HTTPException(404, "Timetable not found")
    if v.hard_violations: raise HTTPException(422, "Timetable with hard violations cannot be submitted")
    if v.status not in ("draft", "rejected"): raise HTTPException(409, f"Cannot submit a {v.status} timetable")
    db.query(ApprovalRecord).filter_by(version_id=v.id).delete()
    depts = {d for (d,) in db.query(Section.department_id).join(TimetableEntry, TimetableEntry.section_id == Section.id)
             .filter(TimetableEntry.version_id == v.id).distinct()}
    for d in depts: db.add(ApprovalRecord(version_id=v.id, department_id=d))
    v.status = "pending"
    notify(db, [h.id for h in db.query(User).filter(User.role == "hod", User.department_id.in_(depts))], "Timetable awaiting approval", v.name)
    db.commit(); return {"version_id": v.id, "departments": sorted(depts)}

@router.get("/approvals")
def list_approvals(user: User = Depends(STAFF), db: Session = Depends(get_db)):
    q = db.query(ApprovalRecord)
    if user.role == "hod": q = q.filter(ApprovalRecord.department_id == user.department_id)
    return [to_dict(a) for a in q.order_by(ApprovalRecord.id.desc())]

def _decide(aid, status, comment, user, db):
    a = db.get(ApprovalRecord, aid)
    if not a: raise HTTPException(404, "Approval not found")
    dept_scope(user, a.department_id)
    if a.status != "pending": raise HTTPException(409, "Already decided")
    a.status, a.decided_by, a.comment, a.decided_at = status, user.id, comment, datetime.utcnow()
    v = db.get(TimetableVersion, a.version_id); db.flush()
    recs = db.query(ApprovalRecord).filter_by(version_id=v.id).all()
    if any(r.status == "rejected" for r in recs): v.status = "rejected"
    elif all(r.status == "approved" for r in recs): v.status = "approved"
    notify(db, [u.id for u in db.query(User).filter_by(role="admin")], f"Timetable {status}", f"{v.name}: {comment or ''}")
    db.commit(); return {**to_dict(a), "version_status": v.status}

@router.post("/approvals/{aid}/approve")
def approve(aid: int, body: CommentIn = CommentIn(), user: User = Depends(STAFF), db: Session = Depends(get_db)):
    return _decide(aid, "approved", body.comment, user, db)

@router.post("/approvals/{aid}/reject")
def reject(aid: int, body: CommentIn = CommentIn(), user: User = Depends(STAFF), db: Session = Depends(get_db)):
    return _decide(aid, "rejected", body.comment, user, db)

# ---------------------------------------------------------------- leave + change requests
@router.post("/leave-requests", status_code=201)
def create_leave(body: LeaveIn, user: User = Depends(FAC), db: Session = Depends(get_db)):
    fp = faculty_profile_of(db, user)
    lr = LeaveRequest(faculty_id=fp.id, **body.model_dump()); db.add(lr)
    notify(db, [h.id for h in db.query(User).filter_by(role="hod", department_id=fp.department_id)], "Leave request", f"{user.full_name}")
    db.commit(); return to_dict(lr)

@router.get("/leave-requests")
def list_leave(user: User = Depends(require_roles("admin", "hod", "faculty")), db: Session = Depends(get_db)):
    q = db.query(LeaveRequest)
    if user.role == "faculty": q = q.filter(LeaveRequest.faculty_id == faculty_profile_of(db, user).id)
    elif user.role == "hod": q = q.join(FacultyProfile, FacultyProfile.id == LeaveRequest.faculty_id).filter(FacultyProfile.department_id == user.department_id)
    return [to_dict(l) for l in q.order_by(LeaveRequest.id.desc())]

@router.post("/leave-requests/{lid}/{decision}")
def decide_leave(lid: int, decision: str, user: User = Depends(STAFF), db: Session = Depends(get_db)):
    if decision not in ("approve", "reject"): raise HTTPException(404, "Unknown action")
    lr = db.get(LeaveRequest, lid)
    if not lr: raise HTTPException(404, "Not found")
    fp = db.get(FacultyProfile, lr.faculty_id); dept_scope(user, fp.department_id)
    if lr.status != "pending": raise HTTPException(409, "Already decided")
    lr.status = "approved" if decision == "approve" else "rejected"; lr.reviewed_by = user.id
    notify(db, [fp.user_id], f"Leave {lr.status}", lr.reason or "")
    db.commit(); return to_dict(lr)

@router.post("/change-requests", status_code=201)
def create_cr(body: ChangeRequestIn, user: User = Depends(require_roles("faculty", "hod")), db: Session = Depends(get_db)):
    cr = TimetableChangeRequest(requested_by=user.id, **body.model_dump()); db.add(cr)
    notify(db, [a.id for a in db.query(User).filter_by(role="admin")], "Timetable change requested", body.description[:100])
    db.commit(); return to_dict(cr)

@router.get("/change-requests")
def list_cr(user: User = Depends(require_roles("admin", "hod", "faculty")), db: Session = Depends(get_db)):
    q = db.query(TimetableChangeRequest)
    if user.role != "admin": q = q.filter(TimetableChangeRequest.requested_by == user.id)
    return [to_dict(c) for c in q.order_by(TimetableChangeRequest.id.desc())]

@router.post("/change-requests/{cid}/resolve")
def resolve_cr(cid: int, body: CommentIn, user: User = Depends(ADMIN), db: Session = Depends(get_db)):
    c = db.get(TimetableChangeRequest, cid)
    if not c: raise HTTPException(404, "Not found")
    c.status, c.response_note = "done", body.comment; notify(db, [c.requested_by], "Change request resolved", body.comment or "")
    db.commit(); return to_dict(c)

# ---------------------------------------------------------------- notifications + dashboard
@router.get("/notifications")
def notifications(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [to_dict(n) for n in db.query(Notification).filter_by(user_id=user.id).order_by(Notification.id.desc()).limit(50)]

@router.post("/notifications/{nid}/read")
def read_notification(nid: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    n = db.get(Notification, nid)
    if not n or n.user_id != user.id: raise HTTPException(404, "Not found")
    n.is_read = True; db.commit(); return {"ok": True}

@router.get("/dashboard")
def dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    pub = db.query(TimetableVersion).filter_by(status="published").first()
    base = {"published_version_id": pub.id if pub else None, "published_name": pub.name if pub else None}
    if user.role == "admin":
        return {**base, "departments": db.query(Department).count(), "faculty": db.query(FacultyProfile).count(),
                "students": db.query(StudentProfile).count(), "subjects": db.query(Subject).count(),
                "rooms": db.query(Room).count(), "sections": db.query(Section).count(),
                "versions": db.query(TimetableVersion).count(), "runs": db.query(OptimizationRun).count(),
                "pending_approvals": db.query(ApprovalRecord).filter_by(status="pending").count(),
                "pending_requests": db.query(TimetableChangeRequest).filter_by(status="pending").count()}
    if user.role == "hod":
        d = user.department_id
        return {**base, "faculty": db.query(FacultyProfile).filter_by(department_id=d).count(),
                "subjects": db.query(Subject).filter_by(department_id=d).count(), "sections": db.query(Section).filter_by(department_id=d).count(),
                "pending_approvals": db.query(ApprovalRecord).filter_by(department_id=d, status="pending").count()}
    if user.role == "faculty":
        fp = faculty_profile_of(db, user)
        rows = db.query(SubjectAssignment).filter_by(faculty_id=fp.id).all()
        hours = 0
        if pub:
            hours = sum(e.duration for e in db.query(TimetableEntry).filter_by(version_id=pub.id, faculty_id=fp.id))
        return {**base, "subjects_assigned": len(rows), "weekly_hours": hours, "max_weekly_hours": fp.max_weekly_hours}
    return base
