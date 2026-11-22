from sqlalchemy.orm import Session

from ..models import ActivityLog


def log_activity(db: Session, user_id: int | None, action: str) -> None:
    db.add(ActivityLog(user_id=user_id, action=action))
    db.commit()
