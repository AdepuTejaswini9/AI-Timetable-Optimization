"""Bridge between the database and the optimisation Problem; version persistence."""
import numpy as np
from sqlalchemy.orm import Session
from app.models import *
from app.algorithms.problem import Problem, OBJ_NAMES

def get_settings(db):
    return {s.key: s.value for s in db.query(SystemSetting).all()}

def build_problem(db: Session) -> Problem:
    st = get_settings(db)
    slots = db.query(TimeSlot).all()
    days = (max(s.day for s in slots) + 1) if slots else 5
    periods = (max(s.period for s in slots) + 1) if slots else 6
    ba = int(st["break_after_period"]) if st.get("break_after_period", "").lstrip("-").isdigit() and int(st["break_after_period"]) >= 0 else None
    users = {u.id: u.full_name for u in db.query(User).all()}
    fac_rows = db.query(FacultyProfile).all()
    faculty = {f.id: dict(name=users[f.user_id], department_id=f.department_id, max_daily=f.max_daily_hours,
                          max_weekly=f.max_weekly_hours, unavailable=set(), avoid=set(), prefer=set()) for f in fac_rows}
    for a in db.query(FacultyAvailability).filter_by(is_available=False): 
        if a.faculty_id in faculty: faculty[a.faculty_id]["unavailable"].add((a.day, a.period))
    for pr in db.query(FacultyPreference):
        if pr.faculty_id in faculty: faculty[pr.faculty_id]["avoid" if pr.preference == "avoid" else "prefer"].add((pr.day, pr.period))
    sections = {s.id: dict(name=f"{db.get(Department, s.department_id).code}-{s.name} (Sem {s.semester})", size=s.strength,
                           department_id=s.department_id, semester=s.semester) for s in db.query(Section)}
    subjects = {s.id: dict(name=s.name, code=s.code, hours=s.weekly_hours, is_lab=s.is_lab, block=s.lab_block,
                           department_id=s.department_id) for s in db.query(Subject)}
    rooms = [dict(id=r.id, name=r.name, capacity=r.capacity, is_lab=r.is_lab, available=r.is_available, unavailable=set())
             for r in db.query(Room).order_by(Room.id)]
    assigns = [(a.section_id, a.subject_id, a.faculty_id) for a in db.query(SubjectAssignment).order_by(SubjectAssignment.id)
               if a.section_id in sections and a.subject_id in subjects and a.faculty_id in faculty]
    weights = {n: float(st.get(f"weight_{n}", 1.0)) for n in OBJ_NAMES}
    names = {"faculty": {k: v["name"] for k, v in faculty.items()}, "subject": {k: v["name"] for k, v in subjects.items()},
             "section": {k: v["name"] for k, v in sections.items()}}
    return Problem(days, periods, ba, sections, subjects, faculty, rooms, assigns, weights, names)

def genes_to_entries(prob: Problem, genes, version_id):
    rows = []
    for s, g in zip(prob.sessions, np.asarray(genes).reshape(-1, 3)):
        rows.append(TimetableEntry(version_id=version_id, section_id=s.section_id, subject_id=s.subject_id,
                                   faculty_id=s.faculty_id, room_id=prob.rooms[int(g[2])]["id"], day=int(g[0]),
                                   period=int(g[1]), duration=s.duration, is_lab=s.is_lab))
    return rows

def entries_to_genes(prob: Problem, entries):
    """Map DB entries onto the problem's sessions. Returns (genes, extra_violations).
    Extra violations: REQUIRED_HOURS / INVALID_REFERENCE detected when entries and assignments disagree."""
    room_idx = {r["id"]: i for i, r in enumerate(prob.rooms)}
    genes = np.zeros((len(prob.sessions), 3), dtype=int); extra = []
    groups = {}
    for e in entries: groups.setdefault((e.section_id, e.subject_id), []).append(e)
    assigned = {(s, sub): f for s, sub, f in prob.assignments}
    for key, idxs in prob.by_key.items():
        es = sorted(groups.pop(key, []), key=lambda e: (-e.duration, e.id))
        if len(es) != len(idxs):
            extra.append({"type": "REQUIRED_HOURS", "key": key, "have": sum(e.duration for e in es),
                          "need": sum(prob.sessions[i].duration for i in idxs)})
        for i, e in zip(idxs, es):
            if e.faculty_id != prob.sessions[i].faculty_id: extra.append({"type": "INVALID_REFERENCE", "key": key})
            genes[i] = (e.day, e.period, room_idx.get(e.room_id, -1))
        for i in idxs[len(es):]: genes[i] = (0, 0, 0)
    for key in groups: extra.append({"type": "INVALID_REFERENCE", "key": key})
    return genes, extra

def create_version(db, prob, genes, name, run_id=None, parent_id=None, user_id=None, notes=None, status="draft"):
    h, o = prob.evaluate(genes)
    parent = db.get(TimetableVersion, parent_id) if parent_id else None
    v = TimetableVersion(name=name, run_id=run_id, parent_version_id=parent_id, created_by=user_id, status=status,
                         version_number=(parent.version_number + 1) if parent else 1, hard_violations=h,
                         objectives=dict(zip(OBJ_NAMES, [float(x) for x in o])), notes=notes)
    db.add(v); db.flush()
    db.add_all(genes_to_entries(prob, genes, v.id)); db.commit()
    return v

def notify(db, user_ids, title, message):
    for uid in set(user_ids): db.add(Notification(user_id=uid, title=title, message=message))
