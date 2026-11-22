from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import Alert, HealthRecord, User
from ..schemas import RecordCreate, RecordOut
from ..services import alert_rules, analysis
from ..services.activity import log_activity
from ..timeutil import utcnow

router = APIRouter(prefix="/api/records", tags=["records"])


@router.post("", response_model=dict, status_code=201)
def add_record(data: RecordCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    values = data.model_dump()
    values["recorded_at"] = values["recorded_at"] or utcnow()
    record = HealthRecord(user_id=user.id, **values)
    db.add(record)
    db.commit()
    db.refresh(record)

    # Deterministic safety rules (never AI-generated)
    new_alerts = alert_rules.evaluate_record(analysis.record_to_dict(record))
    for a in new_alerts:
        db.add(Alert(user_id=user.id, record_id=record.id, **a))
    db.commit()
    log_activity(db, user.id, "added health record")
    return {"record": RecordOut.model_validate(record).model_dump(mode="json"), "alerts": new_alerts}


@router.get("", response_model=list[RecordOut])
def list_records(limit: int = 50, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = (select(HealthRecord).where(HealthRecord.user_id == user.id)
         .order_by(HealthRecord.recorded_at.desc()).limit(max(1, min(limit, 500))))
    return list(db.scalars(q))


@router.delete("/{record_id}", status_code=204)
def delete_record(record_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rec = db.get(HealthRecord, record_id)
    if not rec or rec.user_id != user.id:
        raise HTTPException(404, "Record not found.")
    db.delete(rec)
    db.commit()
    log_activity(db, user.id, "deleted health record")
