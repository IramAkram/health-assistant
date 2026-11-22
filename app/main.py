import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from .config import settings
from .database import Base, SessionLocal, engine
from .models import User
from .routers import admin, alerts, assistant, auth, dashboard, records, reports
from .security import hash_password

log = logging.getLogger("health")


def seed_admin() -> None:
    if not (settings.ADMIN_EMAIL and settings.ADMIN_PASSWORD):
        return
    with SessionLocal() as db:
        if not db.scalar(select(User).where(User.email == settings.ADMIN_EMAIL.lower())):
            db.add(User(email=settings.ADMIN_EMAIL.lower(), full_name="Administrator", role="admin",
                        hashed_password=hash_password(settings.ADMIN_PASSWORD)))
            db.commit()
            log.info("Admin account created: %s", settings.ADMIN_EMAIL)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_admin()
    yield


app = FastAPI(title="Agentic AI Smart Health Monitoring", version="1.0.0", lifespan=lifespan,
              description="Personal health tracking with ML risk estimation and a multi-agent wellness assistant.")

for r in (auth.router, records.router, dashboard.router, alerts.router, assistant.router, reports.router, admin.router):
    app.include_router(r)


@app.get("/api/health", tags=["system"])
def health_check():
    return {"status": "ok"}


app.mount("/static", StaticFiles(directory=settings.FRONTEND_DIR), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(settings.FRONTEND_DIR / "index.html")


@app.get("/dashboard", include_in_schema=False)
def dashboard_page():
    return FileResponse(settings.FRONTEND_DIR / "dashboard.html")
