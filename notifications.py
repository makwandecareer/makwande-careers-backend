from __future__ import annotations

from enum import Enum
from fastapi import APIRouter
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class Channel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    IN_APP = "in_app"
    PUSH = "push"


class NotificationRequest(BaseModel):
    recipient: EmailStr | str
    channel: Channel
    subject: str | None = None
    message: str


@router.post("/send")
def send_notification(payload: NotificationRequest):
    """
    Placeholder notification endpoint.
    Integrate with email, SMS, WhatsApp and push providers.
    """
    return {
        "status": "queued",
        "channel": payload.channel,
        "recipient": payload.recipient,
        "message": "Notification queued successfully."
    }


@router.get("/templates")
def notification_templates():
    return {
        "templates": [
            "Interview Invitation",
            "Application Received",
            "Application Status Update",
            "CV Ready",
            "Subscription Renewal Reminder",
            "New Job Match",
            "Password Reset",
        ]
    }
