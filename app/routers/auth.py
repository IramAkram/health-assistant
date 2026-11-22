from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import User
from ..schemas import Token, UserCreate, UserOut, UserUpdate
from ..security import create_access_token, hash_password, verify_password
from ..services.activity import log_activity

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists.")
    user = User(email=email, full_name=data.full_name.strip(), hashed_password=hash_password(data.password),
                date_of_birth=data.date_of_birth, gender=data.gender, height_cm=data.height_cm)
    db.add(user)
    db.commit()
    db.refresh(user)
    log_activity(db, user.id, "registered")
    return user


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == form.username.lower()))
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password.")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account has been deactivated.")
    log_activity(db, user.id, "logged in")
    return Token(access_token=create_access_token(user.id, user.role))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.put("/me", response_model=UserOut)
def update_me(data: UserUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    log_activity(db, user.id, "updated profile")
    return user
