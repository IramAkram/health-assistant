"""Permission-checked backend functions used by the AI agents.

Every function takes the *authenticated* user_id from the server (never from the model),
so an agent can only ever see the current user's own data. Agents never touch the database directly.
"""
from datetime import timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Alert, HealthRecord, Reminder, User
from ..timeutil import utcnow
from . import analysis, ml_service


def _records(db: Session, user_id: int, days: int) -> list[HealthRecord]:
    since = utcnow() - timedelta(days=max(1, min(days, 365)))
    q = select(HealthRecord).where(HealthRecord.user_id == user_id, HealthRecord.recorded_at >= since)
    return list(db.scalars(q.order_by(HealthRecord.recorded_at)))


def health_summary(db: Session, user_id: int, days: int = 30) -> dict[str, Any]:
    recs = [analysis.record_to_dict(r) for r in _records(db, user_id, days)]
    return {"days": days, **analysis.summarize(recs)}


def recent_records(db: Session, user_id: int, limit: int = 10) -> list[dict[str, Any]]:
    q = (select(HealthRecord).where(HealthRecord.user_id == user_id)
         .order_by(HealthRecord.recorded_at.desc()).limit(max(1, min(limit, 50))))
    out = []
    for r in db.scalars(q):
        d = analysis.record_to_dict(r)
        d["recorded_at"] = d["recorded_at"].isoformat()
        out.append(d)
    return out


def diabetes_risk(db: Session, user_id: int) -> dict[str, Any]:
    user = db.get(User, user_id)
    latest_glucose = db.scalar(select(HealthRecord.glucose).where(
        HealthRecord.user_id == user_id, HealthRecord.glucose.is_not(None)).order_by(HealthRecord.recorded_at.desc()).limit(1))
    latest_dia = db.scalar(select(HealthRecord.diastolic).where(
        HealthRecord.user_id == user_id, HealthRecord.diastolic.is_not(None)).order_by(HealthRecord.recorded_at.desc()).limit(1))
    latest_weight = db.scalar(select(HealthRecord.weight_kg).where(
        HealthRecord.user_id == user_id, HealthRecord.weight_kg.is_not(None)).order_by(HealthRecord.recorded_at.desc()).limit(1))
    return ml_service.estimate_diabetes_risk(
        latest_glucose, latest_dia, analysis.bmi(latest_weight, user.height_cm if user else None),
        analysis.age_from_dob(user.date_of_birth if user else None))


def alerts(db: Session, user_id: int, unread_only: bool = False, limit: int = 10) -> list[dict[str, Any]]:
    q = select(Alert).where(Alert.user_id == user_id)
    if unread_only:
        q = q.where(Alert.is_read.is_(False))
    q = q.order_by(Alert.created_at.desc()).limit(max(1, min(limit, 50)))
    return [{"severity": a.severity, "metric": a.metric, "message": a.message,
             "created_at": a.created_at.isoformat(), "is_read": a.is_read} for a in db.scalars(q)]


def reminders(db: Session, user_id: int) -> list[dict[str, Any]]:
    q = select(Reminder).where(Reminder.user_id == user_id).order_by(Reminder.time_of_day)
    return [{"id": r.id, "title": r.title, "time_of_day": r.time_of_day,
             "frequency": r.frequency, "active": r.active} for r in db.scalars(q)]


def create_reminder(db: Session, user_id: int, title: str, time_of_day: str, frequency: str = "daily") -> dict[str, Any]:
    import re
    if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", time_of_day):
        return {"ok": False, "error": "time_of_day must be HH:MM in 24-hour format, e.g. 07:30"}
    if frequency not in ("daily", "weekly"):
        frequency = "daily"
    r = Reminder(user_id=user_id, title=title[:160], time_of_day=time_of_day, frequency=frequency)
    db.add(r)
    db.commit()
    return {"ok": True, "id": r.id, "title": r.title, "time_of_day": r.time_of_day, "frequency": r.frequency}


def user_profile(db: Session, user_id: int) -> dict[str, Any]:
    u = db.get(User, user_id)
    if not u:
        return {}
    last_w = db.scalar(select(HealthRecord.weight_kg).where(
        HealthRecord.user_id == user_id, HealthRecord.weight_kg.is_not(None)).order_by(HealthRecord.recorded_at.desc()).limit(1))
    return {"first_name": u.full_name.split()[0], "age": analysis.age_from_dob(u.date_of_birth), "gender": u.gender,
            "height_cm": u.height_cm, "bmi": analysis.bmi(last_w, u.height_cm), "health_goal": u.health_goal}


def report_link(days: int = 30) -> dict[str, str]:
    return {"download_path": f"/api/reports/pdf?days={days}",
            "note": "The user can download the PDF from the Report tab of the dashboard."}
