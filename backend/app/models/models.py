from datetime import datetime
from sqlalchemy import (Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON,
                        UniqueConstraint, Index, CheckConstraint)
from sqlalchemy.orm import relationship
from app.database.session import Base

def now(): return datetime.utcnow()

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(120), unique=True, nullable=False)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(120), nullable=False)
    role = Column(String(10), nullable=False)  # admin|hod|faculty|student
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)  # used by HOD
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=now)
    __table_args__ = (CheckConstraint("role in ('admin','hod','faculty','student')", name="ck_user_role"),)

class FacultyProfile(Base):
    __tablename__ = "faculty_profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    designation = Column(String(60), default="Assistant Professor")
    max_daily_hours = Column(Integer, default=5, nullable=False)
    max_weekly_hours = Column(Integer, default=18, nullable=False)
    user = relationship("User")

class Section(Base):
    __tablename__ = "sections"
    id = Column(Integer, primary_key=True)
    name = Column(String(40), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    semester = Column(Integer, nullable=False)
    strength = Column(Integer, nullable=False)
    __table_args__ = (UniqueConstraint("name", "department_id", "semester", name="uq_section"),)

class StudentProfile(Base):
    __tablename__ = "student_profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False, index=True)
    roll_no = Column(String(30), unique=True, nullable=False)
    user = relationship("User")

class Subject(Base):
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(120), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    semester = Column(Integer, nullable=False)
    weekly_hours = Column(Integer, nullable=False)
    is_lab = Column(Boolean, default=False, nullable=False)
    lab_block = Column(Integer, default=2, nullable=False)
    __table_args__ = (CheckConstraint("weekly_hours > 0", name="ck_hours"),)

class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True)
    name = Column(String(40), unique=True, nullable=False)
    capacity = Column(Integer, nullable=False)
    is_lab = Column(Boolean, default=False, nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    building = Column(String(60))

class TimeSlot(Base):
    __tablename__ = "time_slots"
    id = Column(Integer, primary_key=True)
    day = Column(Integer, nullable=False)     # 0=Mon
    period = Column(Integer, nullable=False)  # 0-based
    start_time = Column(String(5), nullable=False)
    end_time = Column(String(5), nullable=False)
    __table_args__ = (UniqueConstraint("day", "period", name="uq_slot"),)

class FacultyAvailability(Base):
    __tablename__ = "faculty_availability"
    id = Column(Integer, primary_key=True)
    faculty_id = Column(Integer, ForeignKey("faculty_profiles.id", ondelete="CASCADE"), nullable=False)
    day = Column(Integer, nullable=False)
    period = Column(Integer, nullable=False)
    is_available = Column(Boolean, default=False, nullable=False)
    __table_args__ = (UniqueConstraint("faculty_id", "day", "period", name="uq_avail"),)

class FacultyPreference(Base):
    __tablename__ = "faculty_preferences"
    id = Column(Integer, primary_key=True)
    faculty_id = Column(Integer, ForeignKey("faculty_profiles.id", ondelete="CASCADE"), nullable=False)
    day = Column(Integer, nullable=False)
    period = Column(Integer, nullable=False)
    preference = Column(String(10), nullable=False)  # preferred|avoid
    __table_args__ = (UniqueConstraint("faculty_id", "day", "period", name="uq_pref"),)

class SubjectAssignment(Base):
    __tablename__ = "subject_assignments"
    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False)
    faculty_id = Column(Integer, ForeignKey("faculty_profiles.id"), nullable=False)
    __table_args__ = (UniqueConstraint("subject_id", "section_id", name="uq_assign"),)

class SystemSetting(Base):
    __tablename__ = "system_settings"
    key = Column(String(60), primary_key=True)
    value = Column(String(255), nullable=False)

class OptimizationRun(Base):
    __tablename__ = "optimization_runs"
    id = Column(Integer, primary_key=True)
    algorithm = Column(String(20), nullable=False)  # ga|nsga2|nsga2_ls|incremental
    status = Column(String(20), default="pending", nullable=False)  # pending|running|completed|failed
    outcome = Column(String(30))  # feasible_found|proven_infeasible|search_limit_reached|repaired|repair_failed
    params = Column(JSON)
    progress = Column(JSON)
    history = Column(JSON)
    message = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=now)
    finished_at = Column(DateTime)

class TimetableVersion(Base):
    __tablename__ = "timetable_versions"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    version_number = Column(Integer, default=1)
    status = Column(String(15), default="draft", nullable=False)  # draft|pending|approved|rejected|published|archived
    run_id = Column(Integer, ForeignKey("optimization_runs.id"))
    parent_version_id = Column(Integer, ForeignKey("timetable_versions.id"))
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=now)
    hard_violations = Column(Integer, default=0)
    objectives = Column(JSON)
    notes = Column(Text)

class OptimizationSolution(Base):
    __tablename__ = "optimization_solutions"
    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("optimization_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    rank = Column(Integer, default=0)
    genes = Column(JSON, nullable=False)
    objectives = Column(JSON, nullable=False)
    hard_violations = Column(Integer, default=0)
    is_selected = Column(Boolean, default=False)
    version_id = Column(Integer, ForeignKey("timetable_versions.id"))

class TimetableEntry(Base):
    __tablename__ = "timetable"
    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey("timetable_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    faculty_id = Column(Integer, ForeignKey("faculty_profiles.id"), nullable=False, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    day = Column(Integer, nullable=False)
    period = Column(Integer, nullable=False)
    duration = Column(Integer, default=1, nullable=False)
    is_lab = Column(Boolean, default=False)
    __table_args__ = (Index("ix_tt_slot", "version_id", "day", "period"),)

class ConstraintViolation(Base):
    __tablename__ = "constraint_violations"
    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey("timetable_versions.id", ondelete="CASCADE"), nullable=True)
    run_id = Column(Integer, ForeignKey("optimization_runs.id", ondelete="CASCADE"), nullable=True)
    type = Column(String(40), nullable=False)
    severity = Column(String(10), default="hard")
    faculty_id = Column(Integer); subject_id = Column(Integer); section_id = Column(Integer); room_id = Column(Integer)
    day = Column(Integer); period = Column(Integer)
    explanation = Column(Text); suggestion = Column(Text)
    created_at = Column(DateTime, default=now)

class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    id = Column(Integer, primary_key=True)
    faculty_id = Column(Integer, ForeignKey("faculty_profiles.id"), nullable=False)
    day = Column(Integer, nullable=False)
    period_from = Column(Integer, default=0)
    period_to = Column(Integer, default=99)
    reason = Column(String(255))
    status = Column(String(10), default="pending")  # pending|approved|rejected
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=now)

class TimetableChangeRequest(Base):
    __tablename__ = "timetable_change_requests"
    id = Column(Integer, primary_key=True)
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    version_id = Column(Integer, ForeignKey("timetable_versions.id"))
    request_type = Column(String(20), default="modification")  # modification|reoptimization
    description = Column(Text, nullable=False)
    payload = Column(JSON)
    status = Column(String(10), default="pending")  # pending|done|rejected
    response_note = Column(Text)
    created_at = Column(DateTime, default=now)

class ApprovalRecord(Base):
    __tablename__ = "approval_records"
    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey("timetable_versions.id", ondelete="CASCADE"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    status = Column(String(10), default="pending", nullable=False)  # pending|approved|rejected
    decided_by = Column(Integer, ForeignKey("users.id"))
    comment = Column(Text)
    decided_at = Column(DateTime)
    __table_args__ = (UniqueConstraint("version_id", "department_id", name="uq_approval"),)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(120), nullable=False)
    message = Column(Text)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=now)
