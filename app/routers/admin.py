from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..deps import get_db, require_admin
from ..models import ActivityLog, Alert, HealthRecord, User
from ..schemas import UserOut

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    return {
        "users": db.scalar(select(func.count(User.id))),
        "active_users": db.scalar(select(func.count(User.id)).where(User.is_active.is_(True))),
        "records": db.scalar(select(func.count(HealthRecord.id))),
        "alerts": db.scalar(select(func.count(Alert.id))),
        "critical_alerts": db.scalar(select(func.count(Alert.id)).where(Alert.severity == "critical")),
    }


@router.get("/users", response_model=list[UserOut])
def users(db: Session = Depends(get_db)):
    return list(db.scalars(select(User).order_by(User.created_at.desc())))


@router.patch("/users/{user_id}/active", response_model=UserOut)
def set_active(user_id: int, active: bool, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(404, "User not found.")
    if target.id == admin.id:
        raise HTTPException(400, "You cannot deactivate your own account.")
    target.is_active = active
    db.commit()
    db.refresh(target)
    return target


@router.get("/logs")
def logs(limit: int = 100, db: Session = Depends(get_db)):
    rows = db.scalars(select(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(max(1, min(limit, 500))))
    return [{"id": r.id, "user_id": r.user_id, "action": r.action, "created_at": r.created_at.isoformat()} for r in rows]
