from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.authentication.security import require_roles, current_user, hash_password, faculty_profile_of
from app.models import *
from app.schemas.schemas import *
from app.services.access import to_dict, dept_scope

router = APIRouter(tags=["academic"])
ADMIN = require_roles("admin"); STAFF = require_roles("admin", "hod"); NOT_STUDENT = require_roles("admin", "hod", "faculty")

def commit(db):
    try: db.commit()
    except IntegrityError as e:
        db.rollback(); raise HTTPException(409, "Conflict: duplicate value or record is still referenced") from e

def crud(path, Model, Schema, read_dep, scope_dept=None):
    """Generic CRUD. HOD reads are limited to their department via `scope_dept` (column name)."""
    @router.get(f"/{path}", name=f"list_{path}")
    def lst(user: User = Depends(read_dep), db: Session = Depends(get_db)):
        q = db.query(Model)
        if user.role == "hod" and scope_dept: q = q.filter(getattr(Model, scope_dept) == user.department_id)
        return [to_dict(o) for o in q.order_by(Model.id).all()]
    @router.get(f"/{path}/{{oid}}", name=f"get_{path}")
    def get(oid: int, user: User = Depends(read_dep), db: Session = Depends(get_db)):
        o = db.get(Model, oid)
        if not o: raise HTTPException(404, "Not found")
        if user.role == "hod" and scope_dept: dept_scope(user, getattr(o, scope_dept))
        return to_dict(o)
    @router.post(f"/{path}", status_code=201, name=f"create_{path}")
    def create(body: Schema, user: User = Depends(ADMIN), db: Session = Depends(get_db)):
        o = Model(**body.model_dump()); db.add(o); commit(db); return to_dict(o)
    @router.put(f"/{path}/{{oid}}", name=f"update_{path}")
    def update(oid: int, body: Schema, user: User = Depends(ADMIN), db: Session = Depends(get_db)):
        o = db.get(Model, oid)
        if not o: raise HTTPException(404, "Not found")
        for k, v in body.model_dump().items(): setattr(o, k, v)
        commit(db); return to_dict(o)
    @router.delete(f"/{path}/{{oid}}", status_code=204, name=f"delete_{path}")
    def delete(oid: int, user: User = Depends(ADMIN), db: Session = Depends(get_db)):
        o = db.get(Model, oid)
        if not o: raise HTTPException(404, "Not found")
        db.delete(o); commit(db)

crud("departments", Department, DepartmentIn, NOT_STUDENT, "id")
crud("subjects", Subject, SubjectIn, NOT_STUDENT, "department_id")
crud("rooms", Room, RoomIn, NOT_STUDENT)
crud("sections", Section, SectionIn, NOT_STUDENT, "department_id")
crud("assignments", SubjectAssignment, AssignmentIn, STAFF)

# ---------------------------------------------------------------- user-backed entities
def _new_user(db, body, role, dept=None):
    if db.query(User).filter(User.email == body.email.lower()).first(): raise HTTPException(409, "Email already registered")
    u = User(email=body.email.lower(), full_name=body.full_name, role=role, department_id=dept,
             password_hash=hash_password(body.password or "ChangeMe@123"))
    db.add(u); db.flush(); return u

def _fac(db, fp):
    u = db.get(User, fp.user_id)
    return {"id": fp.id, "user_id": u.id, "email": u.email, "full_name": u.full_name, "department_id": fp.department_id,
            "designation": fp.designation, "max_daily_hours": fp.max_daily_hours, "max_weekly_hours": fp.max_weekly_hours}

@router.get("/faculty")
def list_faculty(user: User = Depends(STAFF), db: Session = Depends(get_db)):
    q = db.query(FacultyProfile)
    if user.role == "hod": q = q.filter(FacultyProfile.department_id == user.department_id)
    return [_fac(db, f) for f in q.order_by(FacultyProfile.id)]

@router.get("/faculty/{fid}")
def get_faculty(fid: int, user: User = Depends(NOT_STUDENT), db: Session = Depends(get_db)):
    fp = db.get(FacultyProfile, fid)
    if not fp: raise HTTPException(404, "Not found")
    if user.role == "hod": dept_scope(user, fp.department_id)
    if user.role == "faculty" and fp.user_id != user.id: raise HTTPException(403, "Faculty may only view their own profile")
    return _fac(db, fp)

@router.post("/faculty", status_code=201)
def create_faculty(body: FacultyIn, user: User = Depends(ADMIN), db: Session = Depends(get_db)):
    u = _new_user(db, body, "faculty")
    fp = FacultyProfile(user_id=u.id, department_id=body.department_id, designation=body.designation,
                        max_daily_hours=body.max_daily_hours, max_weekly_hours=body.max_weekly_hours)
    db.add(fp); commit(db); return _fac(db, fp)

@router.put("/faculty/{fid}")
def update_faculty(fid: int, body: FacultyIn, user: User = Depends(ADMIN), db: Session = Depends(get_db)):
    fp = db.get(FacultyProfile, fid)
    if not fp: raise HTTPException(404, "Not found")
    u = db.get(User, fp.user_id); u.full_name = body.full_name; u.email = body.email.lower()
    if body.password: u.password_hash = hash_password(body.password)
    fp.department_id, fp.designation = body.department_id, body.designation
    fp.max_daily_hours, fp.max_weekly_hours = body.max_daily_hours, body.max_weekly_hours
    commit(db); return _fac(db, fp)

@router.delete("/faculty/{fid}", status_code=204)
def delete_faculty(fid: int, user: User = Depends(ADMIN), db: Session = Depends(get_db)):
    fp = db.get(FacultyProfile, fid)
    if not fp: raise HTTPException(404, "Not found")
    u = db.get(User, fp.user_id); db.delete(fp); db.flush(); db.delete(u); commit(db)

@router.get("/hods")
def list_hods(user: User = Depends(ADMIN), db: Session = Depends(get_db)):
    return [to_dict(u) for u in db.query(User).filter_by(role="hod").order_by(User.id)]

@router.post("/hods", status_code=201)
def create_hod(body: HodIn, user: User = Depends(ADMIN), db: Session = Depends(get_db)):
    u = _new_user(db, body, "hod", body.department_id); commit(db); return to_dict(u)

@router.put("/hods/{uid}")
def update_hod(uid: int, body: HodIn, user: User = Depends(ADMIN), db: Session = Depends(get_db)):
    u = db.get(User, uid)
    if not u or u.role != "hod": raise HTTPException(404, "Not found")
    u.full_name, u.email, u.department_id = body.full_name, body.email.lower(), body.department_id
    if body.password: u.password_hash = hash_password(body.password)
    commit(db); return to_dict(u)

@router.delete("/hods/{uid}", status_code=204)
def delete_hod(uid: int, user: User = Depends(ADMIN), db: Session = Depends(get_db)):
    u = db.get(User, uid)
    if not u or u.role != "hod": raise HTTPException(404, "Not found")
    db.delete(u); commit(db)

def _stu(db, sp):
    u = db.get(User, sp.user_id)
    return {"id": sp.id, "user_id": u.id, "email": u.email, "full_name": u.full_name, "section_id": sp.section_id, "roll_no": sp.roll_no}

@router.get("/students")
def list_students(user: User = Depends(STAFF), db: Session = Depends(get_db)):
    q = db.query(StudentProfile)
    if user.role == "hod":
        q = q.join(Section, Section.id == StudentProfile.section_id).filter(Section.department_id == user.department_id)
    return [_stu(db, s) for s in q.order_by(StudentProfile.id)]

@router.post("/students", status_code=201)
def create_student(body: StudentIn, user: User = Depends(ADMIN), db: Session = Depends(get_db)):
    u = _new_user(db, body, "student"); sp = StudentProfile(user_id=u.id, section_id=body.section_id, roll_no=body.roll_no)
    db.add(sp); commit(db); return _stu(db, sp)

@router.put("/students/{sid}")
def update_student(sid: int, body: StudentIn, user: User = Depends(ADMIN), db: Session = Depends(get_db)):
    sp = db.get(StudentProfile, sid)
    if not sp: raise HTTPException(404, "Not found")
    u = db.get(User, sp.user_id); u.full_name, u.email = body.full_name, body.email.lower()
    if body.password: u.password_hash = hash_password(body.password)
    sp.section_id, sp.roll_no = body.section_id, body.roll_no
    commit(db); return _stu(db, sp)

@router.delete("/students/{sid}", status_code=204)
def delete_student(sid: int, user: User = Depends(ADMIN), db: Session = Depends(get_db)):
    sp = db.get(StudentProfile, sid)
    if not sp: raise HTTPException(404, "Not found")
    u = db.get(User, sp.user_id); db.delete(sp); db.flush(); db.delete(u); commit(db)

# ---------------------------------------------------------------- availability / config
def _check_fac_access(db, user, fid, write):
    fp = db.get(FacultyProfile, fid)
    if not fp: raise HTTPException(404, "Faculty not found")
    if user.role == "faculty" and fp.user_id != user.id: raise HTTPException(403, "Not your profile")
    if user.role == "hod":
        dept_scope(user, fp.department_id)
        if write: raise HTTPException(403, "HOD cannot edit availability")
    return fp

@router.get("/faculty/{fid}/availability")
def get_availability(fid: int, user: User = Depends(NOT_STUDENT), db: Session = Depends(get_db)):
    _check_fac_access(db, user, fid, False)
    un = [{"day": a.day, "period": a.period} for a in db.query(FacultyAvailability).filter_by(faculty_id=fid, is_available=False)]
    pr = db.query(FacultyPreference).filter_by(faculty_id=fid).all()
    return {"unavailable": un, "avoid": [{"day": p.day, "period": p.period} for p in pr if p.preference == "avoid"],
            "preferred": [{"day": p.day, "period": p.period} for p in pr if p.preference == "preferred"]}

@router.put("/faculty/{fid}/availability")
def put_availability(fid: int, body: AvailabilityIn, user: User = Depends(NOT_STUDENT), db: Session = Depends(get_db)):
    _check_fac_access(db, user, fid, True)
    db.query(FacultyAvailability).filter_by(faculty_id=fid).delete(); db.query(FacultyPreference).filter_by(faculty_id=fid).delete()
    seen = set()
    for s in body.unavailable:
        if (s.day, s.period) not in seen: seen.add((s.day, s.period)); db.add(FacultyAvailability(faculty_id=fid, day=s.day, period=s.period, is_available=False))
    pseen = set()
    for kind, lst in (("avoid", body.avoid), ("preferred", body.preferred)):
        for s in lst:
            if (s.day, s.period) not in pseen: pseen.add((s.day, s.period)); db.add(FacultyPreference(faculty_id=fid, day=s.day, period=s.period, preference=kind))
    commit(db); return get_availability(fid, user, db)

@router.get("/config/timeslots")
def get_slots(user: User = Depends(current_user), db: Session = Depends(get_db)):
    st = {s.key: s.value for s in db.query(SystemSetting)}
    return {"slots": [to_dict(s) for s in db.query(TimeSlot).order_by(TimeSlot.day, TimeSlot.period)],
            "break_after_period": int(st.get("break_after_period", -1))}

@router.put("/config/timeslots")
def put_slots(body: TimeSlotConfig, user: User = Depends(ADMIN), db: Session = Depends(get_db)):
    if db.query(TimetableVersion).filter(TimetableVersion.status == "published").first():
        raise HTTPException(409, "Cannot change the period grid while a timetable is published")
    db.query(TimeSlot).delete()
    h, m = map(int, body.first_start.split(":")); t = h * 60 + m
    for p in range(body.periods):
        a, b = t, t + body.period_minutes
        for d in range(body.days): db.add(TimeSlot(day=d, period=p, start_time=f"{a//60:02d}:{a%60:02d}", end_time=f"{b//60:02d}:{b%60:02d}"))
        t = b + body.gap_minutes + (body.lunch_minutes if p == body.break_after_period else 0)
    s = db.get(SystemSetting, "break_after_period") or SystemSetting(key="break_after_period", value="-1")
    s.value = str(body.break_after_period if body.break_after_period is not None else -1); db.add(s)
    commit(db); return get_slots(user, db)

ALLOWED = {"break_after_period", "weight_student_free_periods", "weight_faculty_preference_violations",
           "weight_excess_consecutive_teaching", "weight_room_underutilization", "weight_subject_distribution"}

@router.get("/settings")
def get_settings_ep(user: User = Depends(STAFF), db: Session = Depends(get_db)):
    return {s.key: s.value for s in db.query(SystemSetting)}

@router.put("/settings")
def put_settings(body: SettingsIn, user: User = Depends(ADMIN), db: Session = Depends(get_db)):
    for k, v in body.values.items():
        if k not in ALLOWED: raise HTTPException(422, f"Unknown setting {k}")
        try: float(v)
        except (TypeError, ValueError): raise HTTPException(422, f"{k} must be numeric")
        row = db.get(SystemSetting, k) or SystemSetting(key=k, value="0"); row.value = str(v); db.add(row)
    commit(db); return get_settings_ep(user, db)
