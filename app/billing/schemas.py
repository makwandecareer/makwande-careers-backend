from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class CheckoutRequest(BaseModel):
    plan_code: str = Field(pattern="^(trial_14_day|premium_30_day)$")
    email: EmailStr


class VerifyRequest(BaseModel):
    reference: str = Field(min_length=8, max_length=120)


class CancelRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class AdminReconcileRequest(BaseModel):
    reference: str = Field(min_length=8, max_length=120)
