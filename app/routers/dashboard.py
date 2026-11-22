from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import Alert, HealthRecord, User
from ..services import analysis, tools
from ..timeutil import utcnow

router = APIRouter(prefix="/api", tags=["dashboard"])
PERIOD_DAYS = {"daily": 1, "weekly": 7, "monthly": 30}


@router.get("/dashboard")
def dashboard(period: Literal["daily", "weekly", "monthly"] = "weekly",
              user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    since = utcnow() - timedelta(days=PERIOD_DAYS[period])
    recs = [analysis.record_to_dict(r) for r in db.scalars(
        select(HealthRecord).where(HealthRecord.user_id == user.id, HealthRecord.recorded_at >= since)
        .order_by(HealthRecord.recorded_at))]
    last_weight = db.scalar(select(HealthRecord.weight_kg).where(
        HealthRecord.user_id == user.id, HealthRecord.weight_kg.is_not(None))
        .order_by(HealthRecord.recorded_at.desc()).limit(1))
    unread = db.scalar(select(func.count(Alert.id)).where(Alert.user_id == user.id, Alert.is_read.is_(False)))
    return {
        "period": period,
        "summary": analysis.summarize(recs),
        "series": analysis.build_series(recs, period),
        "bmi": analysis.bmi(last_weight, user.height_cm),
        "unread_alerts": unread or 0,
    }


@router.get("/risk/diabetes")
def diabetes_risk(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return tools.diabetes_risk(db, user.id)
