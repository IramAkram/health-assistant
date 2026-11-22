from datetime import timedelta

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import Alert, HealthRecord, User
from ..services import analysis, report_service, tools
from ..services.activity import log_activity
from ..timeutil import utcnow

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/pdf")
def download_pdf(days: int = Query(30, ge=1, le=365), user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    since = utcnow() - timedelta(days=days)
    recs = [analysis.record_to_dict(r) for r in db.scalars(
        select(HealthRecord).where(HealthRecord.user_id == user.id, HealthRecord.recorded_at >= since)
        .order_by(HealthRecord.recorded_at))]
    alerts = [{"created_at": a.created_at, "severity": a.severity, "message": a.message} for a in db.scalars(
        select(Alert).where(Alert.user_id == user.id, Alert.created_at >= since).order_by(Alert.created_at.desc()))]
    profile = tools.user_profile(db, user.id)
    pdf = report_service.build_pdf(
        {"full_name": user.full_name, "age": profile["age"], "height_cm": user.height_cm,
         "bmi": profile["bmi"], "health_goal": user.health_goal},
        days, analysis.summarize(recs), recs, alerts, tools.diabetes_risk(db, user.id))
    log_activity(db, user.id, f"downloaded {days}-day report")
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="health_report_{days}d.pdf"'})
