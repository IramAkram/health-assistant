import re
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=72)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = Field(default=None, ge=50, le=250)


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = Field(default=None, ge=50, le=250)
    health_goal: Optional[str] = Field(default=None, max_length=255)
    notifications_consent: Optional[bool] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    date_of_birth: Optional[date]
    gender: Optional[str]
    height_cm: Optional[float]
    health_goal: Optional[str]
    notifications_consent: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RecordCreate(BaseModel):
    recorded_at: Optional[datetime] = None
    systolic: Optional[int] = Field(default=None, ge=50, le=260)
    diastolic: Optional[int] = Field(default=None, ge=30, le=160)
    glucose: Optional[float] = Field(default=None, ge=20, le=700, description="mg/dL")
    weight_kg: Optional[float] = Field(default=None, ge=20, le=400)
    sleep_hours: Optional[float] = Field(default=None, ge=0, le=24)
    exercise_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    stress_level: Optional[int] = Field(default=None, ge=1, le=10)
    notes: Optional[str] = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def _need_one_value(self):
        fields = ["systolic", "diastolic", "glucose", "weight_kg", "sleep_hours", "exercise_minutes", "stress_level"]
        if all(getattr(self, f) is None for f in fields):
            raise ValueError("Enter at least one measurement.")
        if (self.systolic is None) != (self.diastolic is None):
            raise ValueError("Enter both systolic and diastolic blood pressure together.")
        if self.systolic is not None and self.diastolic is not None and self.diastolic >= self.systolic:
            raise ValueError("Diastolic pressure must be lower than systolic pressure.")
        return self


class RecordOut(RecordCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    recorded_at: datetime


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    record_id: Optional[int]
    severity: str
    metric: str
    message: str
    is_read: bool
    created_at: datetime


class ReminderCreate(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    time_of_day: str = Field(description="HH:MM, 24-hour")
    frequency: Literal["daily", "weekly"] = "daily"

    @field_validator("time_of_day")
    @classmethod
    def _check_time(cls, v: str) -> str:
        if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", v):
            raise ValueError("time_of_day must look like 07:30")
        return v


class ReminderOut(ReminderCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    active: bool


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    reply: str
    mode: Literal["agents", "demo"]
