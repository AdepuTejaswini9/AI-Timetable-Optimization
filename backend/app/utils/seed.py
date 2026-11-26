"""Development seed data for a fictional college. DEV-ONLY credentials (see README)."""
from sqlalchemy.orm import Session
from app.authentication.security import hash_password
from app.models import *

PERIOD_TIMES = [("09:00", "09:50"), ("10:00", "10:50"), ("11:00", "11:50"),
                ("13:00", "13:50"), ("14:00", "14:50"), ("15:00", "15:50")]
BREAK_AFTER = 2  # lunch break after period index 2

def _user(db, email, name, role, pw, dept=None):
    u = User(email=email, full_name=name, role=role, password_hash=hash_password(pw), department_id=dept)
    db.add(u); db.flush(); return u

def seed(db: Session):
    if db.query(User).count(): return
    cse = Department(code="CSE", name="Computer Science & Engineering"); ece = Department(code="ECE", name="Electronics & Communication Engineering")
    db.add_all([cse, ece]); db.flush()
    for d in range(5):
        for p, (a, b) in enumerate(PERIOD_TIMES): db.add(TimeSlot(day=d, period=p, start_time=a, end_time=b))
    db.add_all([SystemSetting(key="break_after_period", value=str(BREAK_AFTER))] +
               [SystemSetting(key=f"weight_{n}", value="1.0") for n in
                ["student_free_periods", "faculty_preference_violations", "excess_consecutive_teaching",
                 "room_underutilization", "subject_distribution"]])
    _user(db, "admin@college.edu", "System Admin", "admin", "Admin@123")
    _user(db, "hod.cse@college.edu", "Dr. Ravi Kumar (HOD CSE)", "hod", "Hod@123", cse.id)
    _user(db, "hod.ece@college.edu", "Dr. Sunita Rao (HOD ECE)", "hod", "Hod@123", ece.id)
    fac_def = [("Dr. Anil Sharma", cse), ("Prof. Meera Iyer", cse), ("Dr. Kiran Reddy", cse), ("Prof. Lakshmi Devi", cse),
               ("Dr. Suresh Babu", cse), ("Dr. Priya Nair", ece), ("Prof. Rahul Verma", ece), ("Dr. Anita Das", ece),
               ("Prof. Vikram Singh", ece), ("Dr. Neha Gupta", ece)]
    F = []
    for i, (n, dep) in enumerate(fac_def, 1):
        u = _user(db, f"faculty{i}@college.edu", n, "faculty", "Faculty@123")
        fp = FacultyProfile(user_id=u.id, department_id=dep.id, max_daily_hours=5, max_weekly_hours=18); db.add(fp); db.flush(); F.append(fp)
    rooms = [("R101", 60, False), ("R102", 60, False), ("R103", 70, False), ("R104", 50, False), ("R105", 45, False),
             ("LAB-1", 60, True), ("LAB-2", 60, True)]
    for n, c, lab in rooms: db.add(Room(name=n, capacity=c, is_lab=lab, building="Main Block"))
    sa = Section(name="A", department_id=cse.id, semester=3, strength=55); sb = Section(name="B", department_id=cse.id, semester=3, strength=50)
    sc = Section(name="A", department_id=ece.id, semester=3, strength=45); db.add_all([sa, sb, sc]); db.flush()
    S = {}
    spec = [("CS301", "Data Structures", cse, 4, False), ("CS302", "Database Management Systems", cse, 4, False),
            ("CS303", "Operating Systems", cse, 3, False), ("CS304", "Computer Networks", cse, 3, False),
            ("CS305L", "Data Structures Lab", cse, 4, True),
            ("EC301", "Signals & Systems", ece, 4, False), ("EC302", "Digital Electronics", ece, 4, False),
            ("EC303", "Electromagnetic Theory", ece, 3, False), ("EC304", "Analog Circuits", ece, 3, False),
            ("EC305L", "Electronics Lab", ece, 4, True)]
    for code, name, dep, h, lab in spec:
        s = Subject(code=code, name=name, department_id=dep.id, semester=3, weekly_hours=h, is_lab=lab, lab_block=2); db.add(s); db.flush(); S[code] = s
    teach = {"CS301": F[0], "CS302": F[1], "CS303": F[2], "CS304": F[3], "CS305L": F[4],
             "EC301": F[5], "EC302": F[6], "EC303": F[7], "EC304": F[8], "EC305L": F[9]}
    for code, s in S.items():
        for sec in ([sa, sb] if code.startswith("CS") else [sc]):
            db.add(SubjectAssignment(subject_id=s.id, section_id=sec.id, faculty_id=teach[code].id))
    # availability (unavailable) and preferences (avoid)
    db.add_all([FacultyAvailability(faculty_id=F[0].id, day=4, period=p, is_available=False) for p in (3, 4, 5)])
    db.add_all([FacultyAvailability(faculty_id=F[5].id, day=0, period=0, is_available=False)])
    db.add_all([FacultyPreference(faculty_id=F[1].id, day=d, period=5, preference="avoid") for d in range(5)])
    db.add_all([FacultyPreference(faculty_id=F[2].id, day=d, period=0, preference="avoid") for d in range(5)])
    for i, (sec, n) in enumerate([(sa, "Asha"), (sa, "Bharat"), (sb, "Chitra"), (sb, "Dev"), (sc, "Esha"), (sc, "Farhan")], 1):
        u = _user(db, f"student{i}@college.edu", n + " Student", "student", "Student@123")
        db.add(StudentProfile(user_id=u.id, section_id=sec.id, roll_no=f"22{sec.department_id}{sec.id}{i:03d}"))
    db.commit()
