from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


InvitationStatus = Literal["pending", "accepted", "declined", "expired"]
InterviewStatus = Literal[
    "scheduled",
    "completed",
    "cancelled",
    "rescheduled",
    "no_show",
]


class SaveJobRequest(BaseModel):
    job_id: str


class InvitationCreate(BaseModel):
    candidate_user_id: str
    job_id: str | None = None
    message: str | None = Field(default=None, max_length=5000)


class InvitationResponseUpdate(BaseModel):
    status: Literal["accepted", "declined"]


class InterviewCreate(BaseModel):
    candidate_user_id: str
    job_id: str | None = None
    application_id: str | None = None
    scheduled_at: datetime
    duration_minutes: int = Field(default=30, ge=10, le=480)
    meeting_url: str | None = None
    location: str | None = Field(default=None, max_length=300)
    notes: str | None = Field(default=None, max_length=5000)


class InterviewUpdate(BaseModel):
    scheduled_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=10, le=480)
    meeting_url: str | None = None
    location: str | None = Field(default=None, max_length=300)
    notes: str | None = Field(default=None, max_length=5000)
    status: InterviewStatus | None = None


class NotificationReadUpdate(BaseModel):
    is_read: bool = True


class EmployerVerificationUpdate(BaseModel):
    verified: bool


class AdminRoleUpdate(BaseModel):
    role: Literal["candidate", "cv_builder", "employer", "admin"]
