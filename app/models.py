from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base
from .timeutil import utcnow


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="user")  # "user" | "admin"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    height_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    health_goal: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notifications_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    records: Mapped[list["HealthRecord"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    reminders: Mapped[list["Reminder"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class HealthRecord(Base):
    __tablename__ = "health_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    systolic: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    diastolic: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    glucose: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # mg/dL
    weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sleep_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    exercise_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    stress_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-10
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship(back_populates="records")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    record_id: Mapped[Optional[int]] = mapped_column(ForeignKey("health_records.id", ondelete="SET NULL"), nullable=True)
    severity: Mapped[str] = mapped_column(String(20))  # info | warning | critical
    metric: Mapped[str] = mapped_column(String(40))
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped[User] = relationship(back_populates="alerts")


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    time_of_day: Mapped[str] = mapped_column(String(5))  # "HH:MM"
    frequency: Mapped[str] = mapped_column(String(20), default="daily")  # daily | weekly
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped[User] = relationship(back_populates="reminders")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
