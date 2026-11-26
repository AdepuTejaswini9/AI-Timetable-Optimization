from datetime import datetime, timedelta
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app import config
from app.database.session import get_db
from app.models import User, FacultyProfile, StudentProfile

oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")

def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode()[:72], bcrypt.gensalt()).decode()

def verify_password(pw: str, hashed: str) -> bool:
    try: return bcrypt.checkpw(pw.encode()[:72], hashed.encode())
    except ValueError: return False

def create_token(user: User) -> str:
    exp = datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user.id), "role": user.role, "exp": exp}, config.SECRET_KEY, algorithm=config.ALGORITHM)

def current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)) -> User:
    err = HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})
    try:
        uid = int(jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])["sub"])
    except (JWTError, KeyError, ValueError):
        raise err
    user = db.get(User, uid)
    if not user or not user.is_active: raise err
    return user

def require_roles(*roles):
    def dep(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have permission for this action")
        return user
    return dep

def faculty_profile_of(db: Session, user: User):
    return db.query(FacultyProfile).filter_by(user_id=user.id).first()

def student_profile_of(db: Session, user: User):
    return db.query(StudentProfile).filter_by(user_id=user.id).first()
