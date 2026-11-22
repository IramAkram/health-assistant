"""Create (or promote) an administrator.  Usage: python scripts/create_admin.py admin@example.com 'StrongPass123'"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import User  # noqa: E402
from app.security import hash_password  # noqa: E402

if len(sys.argv) != 3:
    sys.exit("Usage: python scripts/create_admin.py <email> <password>")
email, password = sys.argv[1].lower(), sys.argv[2]
Base.metadata.create_all(bind=engine)
with SessionLocal() as db:
    u = db.scalar(select(User).where(User.email == email))
    if u:
        u.role, u.hashed_password = "admin", hash_password(password)
    else:
        db.add(User(email=email, full_name="Administrator", role="admin", hashed_password=hash_password(password)))
    db.commit()
print(f"Admin ready: {email}")
