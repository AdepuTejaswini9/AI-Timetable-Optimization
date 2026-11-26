from datetime import datetime
import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.authentication.security import require_roles, current_user
from app.models import *
from app.schemas.schemas import GenerateIn, EditEntryIn
from app.services.access import (to_dict, get_version_or_404, scoped_entries, serialize_entries, can_view_version)
from app.services.data_loader import build_problem, entries_to_genes, create_version, notify
from app.services import optimization_service as svc
from app.algorithms.explain import describe, SUGGEST

router = APIRouter(prefix="/timetable", tags=["timetable"])
ADMIN = require_roles("admin")

def _vdict(v): return to_dict(v)

@router.get("")
def list_versions(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [_vdict(v) for v in db.query(TimetableVersion).order_by(TimetableVersion.id.desc()).all() if can_view_version(user, v)]

@router.post("/generate", status_code=201)
def generate(body: GenerateIn, user: User = Depends(ADMIN), db: Session = Depends(get_db)):
    """Synchronous convenience endpoint: run the optimiser and auto-select the best feasible alternative."""
    run = OptimizationRun(algorithm=body.algorithm, status="pending", params=body.model_dump(), created_by=user.id)
    db.add(run); db.commit()
    svc.execute_run(run.id); db.expire_all(); run = db.get(OptimizationRun, run.id)
    if run.outcome != "feasible_found":
        raise HTTPException(422, {"outcome": run.outcome, "message": run.message, "run_id": run.id})
    sols = db.query(OptimizationSolution).filter_by(run_id=run.id).all()
    best = min(sols, key=lambda s: sum(s.objectives.values()))
    v = svc.select_solution(db, run, best, user.id, body.name)
    return {"version_id": v.id, "run_id": run.id, "objectives": v.objectives}

def _conflicts(db, user, v):
    prob = build_problem(db)
    entries = db.query(TimetableEntry).filter_by(version_id=v.id).all()
    genes, extra = entries_to_genes(prob, entries)
    out = []
    ents = {}
    for x in extra:
        sec, sub = x["key"]; typ = x["type"]
        out.append({"type": typ, "severity": "hard", "section_id": sec, "subject_id": sub, "section": prob.names["section"].get(sec),
                    "subject": prob.names["subject"].get(sub), "faculty": None, "room": None, "day": None, "period": None, "slot": "-",
                    "explanation": (f"Subject hours mismatch: scheduled {x.get('have')}h, required {x.get('need')}h." if typ == "REQUIRED_HOURS"
                                   else "Entry does not match a valid subject assignment."), "suggestion": SUGGEST[typ]})
    out += describe(prob, genes) if not extra else []
    if user.role == "hod":
        dept_secs = {sid for sid, s in prob.sections.items() if s["department_id"] == user.department_id}
        out = [o for o in out if o.get("section_id") in dept_secs]
    for o in out: o.pop("sessions", None)
    return out

@router.get("/{vid}/conflicts")
def conflicts(vid: int, user: User = Depends(require_roles("admin", "hod")), db: Session = Depends(get_db)):
    v = get_version_or_404(db, user, vid)
    c = _conflicts(db, user, v)
    return {"version_id": vid, "hard_violation_count": len(c), "violations": c}

@router.get("/{vid}")
def get_timetable(vid: int, section_id: int | None = None, faculty_id: int | None = None, room_id: int | None = None,
                  department_id: int | None = None, semester: int | None = None,
                  user: User = Depends(current_user), db: Session = Depends(get_db)):
    v = get_version_or_404(db, user, vid)
    ents = scoped_entries(db, user, vid, section_id, faculty_id, room_id, department_id, semester)
    slots = db.query(TimeSlot).order_by(TimeSlot.day, TimeSlot.period).all()
    return {"version": _vdict(v), "entries": serialize_entries(db, ents),
            "grid": {"days": max((s.day for s in slots), default=4) + 1,
                     "periods": [{"period": s.period, "start": s.start_time, "end": s.end_time} for s in slots if s.day == 0]}}

@router.put("/{vid}")
def edit_entry(vid: int, body: EditEntryIn, user: User = Depends(ADMIN), db: Session = Depends(get_db)):
    """Manual override – the complete resulting timetable must pass the hard-constraint validator before saving."""
    v = db.get(TimetableVersion, vid)
    if not v: raise HTTPException(404, "Timetable not found")
    if v.status not in ("draft", "rejected"):
        raise HTTPException(409, "Only draft/rejected timetables can be edited; create a copy (POST /timetable/{id}/clone)")
    e = db.get(TimetableEntry, body.entry_id)
    if not e or e.version_id != vid: raise HTTPException(404, "Entry not found in this timetable")
    if not db.get(Room, body.room_id): raise HTTPException(422, "Unknown room")
    prob = build_problem(db)
    entries = db.query(TimetableEntry).filter_by(version_id=vid).all()
    old = (e.day, e.period, e.room_id); e.day, e.period, e.room_id = body.day, body.period, body.room_id
    genes, extra = entries_to_genes(prob, entries)
    viol = describe(prob, genes) if not extra else [{"type": "INVALID", "explanation": "Timetable is inconsistent with subject assignments."}]
    db.rollback() if viol else None
    if viol:
        raise HTTPException(422, {"message": "Change rejected: it would violate hard constraints", "violations": [{k: x[k] for k in x if k != "sessions"} for x in viol]})
    h, o = prob.evaluate(genes); v.hard_violations = h
    from app.algorithms.problem import OBJ_NAMES
    v.objectives = dict(zip(OBJ_NAMES, [float(x) for x in o])); v.status = "draft"
    db.query(ApprovalRecord).filter_by(version_id=vid).delete(); db.commit()
    return {"ok": True, "objectives": v.objectives}

@router.post("/{vid}/clone", status_code=201)
def clone(vid: int, user: User = Depends(ADMIN), db: Session = Depends(get_db)):
    v = db.get(TimetableVersion, vid)
    if not v: raise HTTPException(404, "Timetable not found")
    prob = build_problem(db); genes, extra = entries_to_genes(prob, db.query(TimetableEntry).filter_by(version_id=vid).all())
    if extra: raise HTTPException(409, "Source timetable inconsistent")
    nv = create_version(db, prob, genes, f"{v.name} (copy)", parent_id=vid, user_id=user.id, notes="Cloned for manual editing")
    return {"version_id": nv.id}

@router.post("/{vid}/publish")
def publish(vid: int, user: User = Depends(ADMIN), db: Session = Depends(get_db)):
    v = db.get(TimetableVersion, vid)
    if not v: raise HTTPException(404, "Timetable not found")
    if v.status == "published": raise HTTPException(409, "Already published")
    # Re-validate against current data – a timetable with hard violations is NEVER published.
    prob = build_problem(db); genes, extra = entries_to_genes(prob, db.query(TimetableEntry).filter_by(version_id=vid).all())
    if extra or prob.hard_count(genes):
        raise HTTPException(422, "Publication blocked: timetable has hard-constraint violations")
    recs = db.query(ApprovalRecord).filter_by(version_id=vid).all()
    if not recs: raise HTTPException(409, "Submit the timetable for HOD approval before publishing")
    if any(r.status != "approved" for r in recs): raise HTTPException(409, "All departments must approve before publication")
    for old in db.query(TimetableVersion).filter(TimetableVersion.status == "published"): old.status = "archived"
    v.status = "published"
    notify(db, [u.id for u in db.query(User).filter(User.role.in_(["faculty", "student", "hod"]))], "Timetable published", f"{v.name} is now live.")
    db.commit(); return _vdict(v)
