"""Creates a demo user with 30 days of realistic readings (great for your viva demo).

Login afterwards with:  demo@example.com / Demo@12345
"""
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import Alert, HealthRecord, Reminder, User  # noqa: E402
from app.security import hash_password  # noqa: E402
from app.services import alert_rules, analysis  # noqa: E402
from app.timeutil import utcnow  # noqa: E402

random.seed(7)
Base.metadata.create_all(bind=engine)
with SessionLocal() as db:
    if db.scalar(select(User).where(User.email == "demo@example.com")):
        sys.exit("Demo user already exists.")
    user = User(email="demo@example.com", full_name="Ayesha Khan", hashed_password=hash_password("Demo@12345"),
                date_of_birth=date(1990, 5, 14), gender="female", height_cm=165,
                health_goal="Lower my blood pressure and sleep 7+ hours", notifications_consent=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    now = utcnow()
    for i in range(30, -1, -1):
        t = (now - timedelta(days=i)).replace(hour=8, minute=random.randint(0, 40), second=0, microsecond=0)
        drift = (30 - i) * 0.25
        rec = HealthRecord(
            user_id=user.id, recorded_at=t,
            systolic=round(122 + drift + random.gauss(0, 5)), diastolic=round(78 + drift / 2 + random.gauss(0, 3)),
            glucose=round(98 + drift * 1.2 + random.gauss(0, 9)), weight_kg=round(71 - i * -0.02 + random.gauss(0, 0.3), 1),
            sleep_hours=round(max(3.5, random.gauss(6.4, 1.0)), 1), exercise_minutes=random.choice([0, 15, 20, 30, 45, 60]),
            stress_level=random.randint(2, 8))
        db.add(rec)
        db.commit()
        db.refresh(rec)
        for a in alert_rules.evaluate_record(analysis.record_to_dict(rec)):
            db.add(Alert(user_id=user.id, record_id=rec.id, created_at=t, **a))
        db.commit()
    db.add_all([Reminder(user_id=user.id, title="Measure blood pressure", time_of_day="08:00", frequency="daily"),
                Reminder(user_id=user.id, title="Evening walk", time_of_day="18:30", frequency="daily")])
    db.commit()
print("Demo data created -> demo@example.com / Demo@12345")
