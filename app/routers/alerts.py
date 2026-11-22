from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import Alert, Reminder, User
from ..schemas import AlertOut, ReminderCreate, ReminderOut

router = APIRouter(prefix="/api", tags=["alerts & reminders"])


@router.get("/alerts", response_model=list[AlertOut])
def list_alerts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list(db.scalars(select(Alert).where(Alert.user_id == user.id).order_by(Alert.created_at.desc()).limit(100)))


@router.post("/alerts/read-all", status_code=204)
def mark_all_read(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    for a in db.scalars(select(Alert).where(Alert.user_id == user.id, Alert.is_read.is_(False))):
        a.is_read = True
    db.commit()


@router.get("/reminders", response_model=list[ReminderOut])
def list_reminders(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list(db.scalars(select(Reminder).where(Reminder.user_id == user.id).order_by(Reminder.time_of_day)))


@router.post("/reminders", response_model=ReminderOut, status_code=201)
def create_reminder(data: ReminderCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = Reminder(user_id=user.id, **data.model_dump())
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


@router.patch("/reminders/{reminder_id}/toggle", response_model=ReminderOut)
def toggle_reminder(reminder_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = db.get(Reminder, reminder_id)
    if not r or r.user_id != user.id:
        raise HTTPException(404, "Reminder not found.")
    r.active = not r.active
    db.commit()
    db.refresh(r)
    return r


@router.delete("/reminders/{reminder_id}", status_code=204)
def delete_reminder(reminder_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = db.get(Reminder, reminder_id)
    if not r or r.user_id != user.id:
        raise HTTPException(404, "Reminder not found.")
    db.delete(r)
    db.commit()
