from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.authentication.security import verify_password, create_token, current_user, faculty_profile_of, student_profile_of
from app.models import User, Section
from app.schemas.schemas import LoginIn

router = APIRouter(prefix="/auth", tags=["auth"])

def _me(db, u):
    d = {"id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role, "department_id": u.department_id}
    if u.role == "faculty":
        fp = faculty_profile_of(db, u)
        if fp: d.update(faculty_id=fp.id, department_id=fp.department_id)
    if u.role == "student":
        sp = student_profile_of(db, u)
        if sp:
            sec = db.get(Section, sp.section_id); d.update(section_id=sp.section_id, department_id=sec.department_id, section_name=sec.name, semester=sec.semester)
    return d

@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.email == body.email.strip().lower()).first()
    if not u or not u.is_active or not verify_password(body.password, u.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    return {"access_token": create_token(u), "token_type": "bearer", "user": _me(db, u)}

@router.get("/me")
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return _me(db, user)
