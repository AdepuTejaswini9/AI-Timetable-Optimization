from typing import Optional, List, Literal
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class LoginIn(BaseModel):
    email: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=1, max_length=128)

class DepartmentIn(BaseModel):
    code: str = Field(min_length=1, max_length=20); name: str = Field(min_length=1, max_length=120)

class SubjectIn(BaseModel):
    code: str = Field(min_length=1, max_length=20); name: str = Field(min_length=1, max_length=120)
    department_id: int; semester: int = Field(ge=1, le=12); weekly_hours: int = Field(ge=1, le=20)
    is_lab: bool = False; lab_block: int = Field(2, ge=1, le=4)

class RoomIn(BaseModel):
    name: str = Field(min_length=1, max_length=40); capacity: int = Field(ge=1, le=1000)
    is_lab: bool = False; is_available: bool = True; building: Optional[str] = None

class SectionIn(BaseModel):
    name: str = Field(min_length=1, max_length=40); department_id: int
    semester: int = Field(ge=1, le=12); strength: int = Field(ge=1, le=500)

class AssignmentIn(BaseModel):
    subject_id: int; section_id: int; faculty_id: int

class FacultyIn(BaseModel):
    email: str = Field(min_length=3, max_length=120); full_name: str = Field(min_length=1, max_length=120)
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    department_id: int; designation: str = "Assistant Professor"
    max_daily_hours: int = Field(5, ge=1, le=10); max_weekly_hours: int = Field(18, ge=1, le=40)

class HodIn(BaseModel):
    email: str = Field(min_length=3, max_length=120); full_name: str = Field(min_length=1, max_length=120)
    password: Optional[str] = Field(None, min_length=8, max_length=128); department_id: int

class StudentIn(BaseModel):
    email: str = Field(min_length=3, max_length=120); full_name: str = Field(min_length=1, max_length=120)
    password: Optional[str] = Field(None, min_length=8, max_length=128); section_id: int; roll_no: str = Field(min_length=1, max_length=30)

class SlotRef(BaseModel):
    day: int = Field(ge=0, le=5); period: int = Field(ge=0, le=15)

class AvailabilityIn(BaseModel):
    unavailable: List[SlotRef] = []; avoid: List[SlotRef] = []; preferred: List[SlotRef] = []

class TimeSlotConfig(BaseModel):
    days: int = Field(5, ge=1, le=6); periods: int = Field(6, ge=1, le=10)
    first_start: str = "09:00"; period_minutes: int = Field(50, ge=20, le=120); gap_minutes: int = Field(10, ge=0, le=30)
    break_after_period: Optional[int] = Field(2, ge=-1, le=9); lunch_minutes: int = Field(60, ge=0, le=120)

class GenerateIn(BaseModel):
    algorithm: Literal["ga", "nsga2", "nsga2_ls"] = "nsga2_ls"
    population: int = Field(40, ge=6, le=200); generations: int = Field(40, ge=1, le=500)
    ls_iterations: int = Field(150, ge=0, le=2000); seed: int = 1; name: Optional[str] = None

class SelectIn(BaseModel):
    solution_id: int

class EditEntryIn(BaseModel):
    entry_id: int; day: int = Field(ge=0, le=5); period: int = Field(ge=0, le=15); room_id: int

class ReoptIn(BaseModel):
    version_id: int; event_type: Literal["faculty", "room"]
    faculty_id: Optional[int] = None; room_id: Optional[int] = None
    slots: Optional[List[SlotRef]] = None  # None => unavailable for the whole week
    persist: bool = False; seed: int = 1; change_request_id: Optional[int] = None; note: Optional[str] = None

class CommentIn(BaseModel):
    comment: Optional[str] = Field(None, max_length=1000)

class SubmitIn(BaseModel):
    version_id: int

class LeaveIn(BaseModel):
    day: int = Field(ge=0, le=5); period_from: int = Field(0, ge=0, le=15); period_to: int = Field(99, ge=0, le=99)
    reason: Optional[str] = Field(None, max_length=255)

class ChangeRequestIn(BaseModel):
    version_id: Optional[int] = None; request_type: Literal["modification", "reoptimization"] = "modification"
    description: str = Field(min_length=3, max_length=2000); payload: Optional[dict] = None

class SettingsIn(BaseModel):
    values: dict
