from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.billing.auth import current_user_id
from app.billing.config import settings
from app.billing.db import SessionLocal
from app.billing.models import BillingPayment, BillingPlan
from app.billing.paystack import paystack
from app.billing.schemas import AdminReconcileRequest, CancelRequest, CheckoutRequest, VerifyRequest
from app.billing.service import (
    cancel_renewal,
    create_checkout,
    expire_due_subscriptions,
    get_current_subscription,
    get_management_link,
    reactivate,
    seed_plans,
    serialize_payment,
    serialize_plan,
    serialize_subscription,
    verify_and_fulfil,
)
from app.billing.webhooks import persist_event, process_event


router = APIRouter(prefix="/billing", tags=["Billing"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/plans")
def list_plans(db: Session = Depends(get_db)) -> dict[str, Any]:
    seed_plans(db)
    plans = db.scalars(
        select(BillingPlan).where(BillingPlan.is_active.is_(True)).order_by(BillingPlan.amount_subunits)
    ).all()
    return {"plans": [serialize_plan(plan) for plan in plans]}


@router.get("/subscription")
def subscription(
    user_id: str = Depends(current_user_id),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return {"subscription": serialize_subscription(get_current_subscription(db, user_id))}


@router.get("/payments")
def payment_history(
    user_id: str = Depends(current_user_id),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    payments = db.scalars(
        select(BillingPayment)
        .where(BillingPayment.user_id == user_id)
        .order_by(desc(BillingPayment.created_at))
        .limit(100)
    ).all()
    return {"payments": [serialize_payment(payment) for payment in payments]}


@router.post("/checkout")
async def checkout(
    body: CheckoutRequest,
    user_id: str = Depends(current_user_id),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return await create_checkout(db, user_id=user_id, email=str(body.email), plan_code=body.plan_code)


@router.post("/verify")
async def verify(
    body: VerifyRequest,
    user_id: str = Depends(current_user_id),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return await verify_and_fulfil(db, user_id=user_id, reference=body.reference)


@router.post("/cancel")
async def cancel(
    body: CancelRequest,
    user_id: str = Depends(current_user_id),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    subscription = await cancel_renewal(db, user_id=user_id, reason=body.reason)
    return {"subscription": serialize_subscription(subscription)}


@router.post("/reactivate")
async def reactivate_subscription(
    user_id: str = Depends(current_user_id),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    subscription = await reactivate(db, user_id=user_id)
    return {"subscription": serialize_subscription(subscription)}


@router.get("/manage-payment-method")
async def manage_payment_method(
    user_id: str = Depends(current_user_id),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    return {"url": await get_management_link(db, user_id=user_id)}


@router.post("/webhook")
async def webhook(
    request: Request,
    x_paystack_signature: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    raw_body = await request.body()
    if not paystack.verify_webhook(raw_body, x_paystack_signature):
        raise HTTPException(status_code=401, detail="Invalid Paystack signature.")

    payload = json.loads(raw_body.decode("utf-8"))
    event_type = str(payload.get("event", "unknown"))
    data = payload.get("data") or {}

    event = persist_event(
        db,
        event_type=event_type,
        data=data,
        payload=payload,
        raw_body=raw_body,
    )
    if event is None:
        return {"received": True}

    process_event(db, event)
    return {"received": True}


@router.post("/internal/expire-subscriptions")
def expire_subscriptions(
    x_billing_cron_secret: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    if not settings.cron_secret or x_billing_cron_secret != settings.cron_secret:
        raise HTTPException(status_code=401, detail="Invalid cron secret.")
    return {"expired": expire_due_subscriptions(db)}


@router.post("/internal/reconcile")
async def reconcile(
    body: AdminReconcileRequest,
    x_billing_cron_secret: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if not settings.cron_secret or x_billing_cron_secret != settings.cron_secret:
        raise HTTPException(status_code=401, detail="Invalid admin secret.")

    payment = db.scalar(select(BillingPayment).where(BillingPayment.reference == body.reference))
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found.")

    return await verify_and_fulfil(db, user_id=payment.user_id, reference=payment.reference)
