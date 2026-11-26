"""Authorization helpers: row scoping for HOD / faculty / student, and entry serialisation."""
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import *

def to_dict(o, exclude=("password_hash",)):
    return {c.key: getattr(o, c.key) for c in o.__table__.columns if c.key not in exclude}

VISIBLE_STATUS = {"hod": {"pending", "approved", "rejected", "published", "archived"},
                  "faculty": {"published"}, "student": {"published"}}

def can_view_version(user, v):
    return user.role == "admin" or v.status in VISIBLE_STATUS.get(user.role, set())

def get_version_or_404(db, user, vid):
    v = db.get(TimetableVersion, vid)
    if not v or not can_view_version(user, v): raise HTTPException(404, "Timetable not found")
    return v

def scoped_entries(db: Session, user, version_id, section_id=None, faculty_id=None, room_id=None,
                   department_id=None, semester=None):
    """Entries the user may see, plus optional filters. Isolation is enforced here, server-side."""
    from app.authentication.security import faculty_profile_of, student_profile_of
    q = db.query(TimetableEntry).join(Section, Section.id == TimetableEntry.section_id).filter(TimetableEntry.version_id == version_id)
    if user.role == "hod":
        q = q.filter(Section.department_id == user.department_id)
    elif user.role == "faculty":
        fp = faculty_profile_of(db, user)
        q = q.filter(TimetableEntry.faculty_id == (fp.id if fp else -1))
    elif user.role == "student":
        sp = student_profile_of(db, user)
        q = q.filter(TimetableEntry.section_id == (sp.section_id if sp else -1))
    if section_id: q = q.filter(TimetableEntry.section_id == section_id)
    if faculty_id: q = q.filter(TimetableEntry.faculty_id == faculty_id)
    if room_id: q = q.filter(TimetableEntry.room_id == room_id)
    if department_id: q = q.filter(Section.department_id == department_id)
    if semester: q = q.filter(Section.semester == semester)
    return q.order_by(TimetableEntry.day, TimetableEntry.period).all()

def name_maps(db):
    users = {u.id: u.full_name for u in db.query(User)}
    return {"faculty": {f.id: users.get(f.user_id) for f in db.query(FacultyProfile)},
            "subject": {s.id: s for s in db.query(Subject)},
            "section": {s.id: s for s in db.query(Section)},
            "room": {r.id: r for r in db.query(Room)},
            "dept": {d.id: d.code for d in db.query(Department)}}

def serialize_entries(db, entries, maps=None):
    m = maps or name_maps(db); out = []
    for e in entries:
        sub, sec, room = m["subject"].get(e.subject_id), m["section"].get(e.section_id), m["room"].get(e.room_id)
        out.append({"id": e.id, "section_id": e.section_id, "section": f"{m['dept'].get(sec.department_id)}-{sec.name}" if sec else None,
                    "semester": sec.semester if sec else None, "department_id": sec.department_id if sec else None,
                    "subject_id": e.subject_id, "subject": sub.name if sub else None, "subject_code": sub.code if sub else None,
                    "faculty_id": e.faculty_id, "faculty": m["faculty"].get(e.faculty_id),
                    "room_id": e.room_id, "room": room.name if room else None, "day": e.day, "period": e.period,
                    "duration": e.duration, "is_lab": bool(e.is_lab)})
    return out

def dept_scope(user, dept_id):
    if user.role == "hod" and dept_id != user.department_id:
        raise HTTPException(403, "Access restricted to your own department")
