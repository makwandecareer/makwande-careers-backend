from __future__ import annotations

from enum import Enum
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/billing", tags=["Payments & Billing"])


class Plan(str, Enum):
    TRIAL_14_DAY = "trial_14_day"
    PREMIUM_30_DAY = "premium_30_day"
    ENTERPRISE = "enterprise"


class CheckoutRequest(BaseModel):
    user_id: int
    plan: Plan
    currency: str = Field(default="ZAR")
    amount: float


@router.post("/checkout")
def create_checkout(payload: CheckoutRequest):
    """
    Placeholder checkout endpoint.
    Integrate with Paystack or another payment gateway.
    """
    return {
        "status": "pending",
        "provider": "paystack",
        "checkout_reference": f"CHK-{payload.user_id}-{payload.plan.value}",
        "amount": payload.amount,
        "currency": payload.currency,
    }


@router.get("/subscription/{user_id}")
def subscription(user_id: int):
    return {
        "user_id": user_id,
        "plan": "premium_30_day",
        "status": "active",
        "renewal_date": "2026-08-30",
        "auto_renew": False,
    }


@router.get("/invoices/{user_id}")
def invoices(user_id: int):
    return {
        "user_id": user_id,
        "invoices": [],
    }


@router.post("/webhook/paystack")
def paystack_webhook():
    return {
        "status": "received",
        "message": "Verify signature and update payment records."
    }
