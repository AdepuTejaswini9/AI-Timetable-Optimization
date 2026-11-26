from datetime import datetime
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.authentication.security import require_roles
from app.models import *
from app.schemas.schemas import GenerateIn, SelectIn, ReoptIn
from app.services.access import to_dict, serialize_entries
from app.services import optimization_service as svc
from app.services.data_loader import build_problem, entries_to_genes, create_version, genes_to_entries, notify
from app.algorithms.reoptimize import reoptimize
from app.algorithms.explain import describe

router = APIRouter(tags=["optimization"])
ADMIN = require_roles("admin"); STAFF = require_roles("admin", "hod")

def _new_run(db, user, body: GenerateIn):
    run = OptimizationRun(algorithm=body.algorithm, status="pending", params=body.model_dump(), created_by=user.id)
    db.add(run); db.commit(); return run

@router.post("/optimization/generate", status_code=202)
def generate(body: GenerateIn, bg: BackgroundTasks, user: User = Depends(ADMIN), db: Session = Depends(get_db)):
    run = _new_run(db, user, body); bg.add_task(svc.execute_run, run.id)
    return {"run_id": run.id, "status": run.status}

@router.get("/optimization")
def list_runs(user: User = Depends(ADMIN), db: Session = Depends(get_db)):
    out = []
    for r in db.query(OptimizationRun).order_by(OptimizationRun.id.desc()).limit(50):
        d = to_dict(r); d.pop("history", None); out.append(d)
    return out

@router.get("/optimization/{rid}/status")
def status(rid: int, user: User = Depends(ADMIN), db: Session = Depends(get_db)):
    r = db.get(OptimizationRun, rid)
    if not r: raise HTTPException(404, "Run not found")
    d = to_dict(r)
    d["violations"] = [to_dict(v) for v in db.query(ConstraintViolation).filter_by(run_id=rid)]
    return d

@router.get("/optimization/{rid}/solutions")
def solutions(rid: int, user: User = Depends(ADMIN), db: Session = Depends(get_db)):
    if not db.get(OptimizationRun, rid): raise HTTPException(404, "Run not found")
    return [{"id": s.id, "rank": s.rank, "objectives": s.objectives, "hard_violations": s.hard_violations,
             "is_selected": s.is_selected, "version_id": s.version_id}
            for s in db.query(OptimizationSolution).filter_by(run_id=rid).order_by(OptimizationSolution.rank)]

@router.get("/optimization/solutions/{sid}/entries")
def solution_entries(sid: int, section_id: int | None = None, user: User = Depends(ADMIN), db: Session = Depends(get_db)):
    s = db.get(OptimizationSolution, sid)
    if not s: raise HTTPException(404, "Solution not found")
    prob = build_problem(db)
    rows = genes_to_entries(prob, np.array(s.genes, dtype=int), 0)
    for i, r in enumerate(rows): r.id = i
    if section_id: rows = [r for r in rows if r.section_id == section_id]
    return serialize_entries(db, rows)

@router.post("/optimization/{rid}/select", status_code=201)
def select(rid: int, body: SelectIn, user: User = Depends(ADMIN), db: Session = Depends(get_db)):
    run = db.get(OptimizationRun, rid); sol = db.get(OptimizationSolution, body.solution_id)
    if not run or not sol or sol.run_id != rid: raise HTTPException(404, "Run or solution not found")
    try: v = svc.select_solution(db, run, sol, user.id)
    except ValueError as e: raise HTTPException(409, str(e))
    return {"version_id": v.id, "status": v.status}

# ------------------------------------------------------------------ incremental re-optimisation
@router.post("/reoptimization/request", status_code=201)
def reopt_request(body: ReoptIn, user: User = Depends(STAFF), db: Session = Depends(get_db)):
    v = db.get(TimetableVersion, body.version_id)
    if not v: raise HTTPException(404, "Timetable version not found")
    if body.event_type == "faculty" and not body.faculty_id or body.event_type == "room" and not body.room_id:
        raise HTTPException(422, "faculty_id / room_id required for the event type")
    if user.role == "hod":  # HOD may only *request*; admin executes
        fp = db.get(FacultyProfile, body.faculty_id) if body.faculty_id else None
        if body.event_type != "faculty" or not fp or fp.department_id != user.department_id:
            raise HTTPException(403, "HOD may request re-optimisation only for faculty of their own department")
        cr = TimetableChangeRequest(requested_by=user.id, version_id=v.id, request_type="reoptimization",
                                    description=body.note or "Re-optimisation requested by HOD", payload=body.model_dump())
        db.add(cr); db.flush()
        notify(db, [a.id for a in db.query(User).filter_by(role="admin")], "Re-optimisation requested", f"Request #{cr.id} from {user.full_name}")
        db.commit(); return {"change_request_id": cr.id, "status": "pending_admin"}
    prob = build_problem(db)
    entries = db.query(TimetableEntry).filter_by(version_id=v.id).all()
    genes, extra = entries_to_genes(prob, entries)
    if extra or prob.hard_count(genes):
        raise HTTPException(409, "Source timetable is not hard-feasible; fix it before re-optimising")
    slots = [[s.day, s.period] for s in body.slots] if body.slots else None
    ev = {"type": body.event_type, "id": body.faculty_id if body.event_type == "faculty" else body.room_id, "slots": slots}
    if body.event_type == "faculty" and body.faculty_id not in prob.faculty or body.event_type == "room" and body.room_id not in [r["id"] for r in prob.rooms]:
        raise HTTPException(404, "Faculty/room not found")
    run = OptimizationRun(algorithm="incremental", status="running", params={**body.model_dump(), "event": ev}, created_by=user.id)
    db.add(run); db.flush()
    res = reoptimize(prob, genes, ev, seed=body.seed)
    out = {"run_id": run.id, "success": res["success"], "reason": res["reason"], "affected": res["affected_details"],
           "unlocked_count": len(res["unlocked"]), "changed_count": len(res["changed"]), "expansion_level": res["level"],
           "original_version_id": v.id, "new_version_id": None, "violations": res["violations"], "suggestions": res.get("suggestions", [])}
    if res["success"]:
        if res["changed"]:
            nv = create_version(db, prob, res["genes"], f"{v.name} (repair v{v.version_number + 1})", run_id=run.id, parent_id=v.id,
                                user_id=user.id, notes=f"Incremental repair: {res['reason']}")
            out["new_version_id"] = nv.id
        if body.persist:  # make the unavailability permanent in master data
            if body.event_type == "faculty":
                for d, p in (slots or [[d, p] for d in range(prob.days) for p in range(prob.periods)]):
                    if not db.query(FacultyAvailability).filter_by(faculty_id=body.faculty_id, day=d, period=p).first():
                        db.add(FacultyAvailability(faculty_id=body.faculty_id, day=d, period=p, is_available=False))
            elif slots is None: db.get(Room, body.room_id).is_available = False
        run.outcome = "repaired"
    else:
        run.outcome = "repair_failed"
        for x in res["violations"]:
            db.add(ConstraintViolation(run_id=run.id, type=x["type"], faculty_id=x["faculty_id"], subject_id=x["subject_id"],
                   section_id=x["section_id"], room_id=x["room_id"], day=x["day"], period=x["period"], explanation=x["explanation"], suggestion=x["suggestion"]))
    run.status, run.message, run.finished_at = "completed", res["reason"], datetime.utcnow()
    run.progress = {k: v2 for k, v2 in out.items() if k != "violations"}
    if body.change_request_id:
        cr = db.get(TimetableChangeRequest, body.change_request_id)
        if cr: cr.status, cr.response_note = "done", res["reason"]
    db.commit(); return out

@router.get("/reoptimization/{rid}/status")
def reopt_status(rid: int, user: User = Depends(ADMIN), db: Session = Depends(get_db)):
    r = db.get(OptimizationRun, rid)
    if not r or r.algorithm != "incremental": raise HTTPException(404, "Re-optimisation run not found")
    d = to_dict(r); d["violations"] = [to_dict(v) for v in db.query(ConstraintViolation).filter_by(run_id=rid)]
    return d
