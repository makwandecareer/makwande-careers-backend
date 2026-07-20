from __future__ import annotations

import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.billing.config import settings
from app.billing.models import (
    BillingAuditLog,
    BillingCustomer,
    BillingPayment,
    BillingPlan,
    BillingSubscription,
)
from app.billing.paystack import paystack


ACTIVE_STATUSES = {"active", "non_renewing", "attention"}


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def seed_plans(db: Session) -> None:
    existing = {row.code for row in db.scalars(select(BillingPlan)).all()}
    now = now_utc()

    if "trial_14_day" not in existing:
        db.add(
            BillingPlan(
                code="trial_14_day",
                name="14-Day Access",
                description="One-time R45 access for 14 days.",
                amount_subunits=4500,
                currency="ZAR",
                access_days=14,
                is_recurring=False,
                created_at=now,
                updated_at=now,
            )
        )

    if "premium_30_day" not in existing:
        db.add(
            BillingPlan(
                code="premium_30_day",
                name="30-Day Premium",
                description="Recurring R300 monthly premium access.",
                amount_subunits=30000,
                currency="ZAR",
                access_days=30,
                is_recurring=True,
                paystack_plan_code=settings.premium_plan_code or None,
                created_at=now,
                updated_at=now,
            )
        )

    db.commit()


def get_plan(db: Session, code: str) -> BillingPlan:
    plan = db.scalar(select(BillingPlan).where(BillingPlan.code == code, BillingPlan.is_active.is_(True)))
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found.")
    return plan


def get_current_subscription(db: Session, user_id: str) -> BillingSubscription | None:
    return db.scalar(
        select(BillingSubscription)
        .where(BillingSubscription.user_id == user_id)
        .order_by(desc(BillingSubscription.created_at))
        .limit(1)
    )


def has_active_access(db: Session, user_id: str) -> bool:
    subscription = get_current_subscription(db, user_id)
    return bool(
        subscription
        and subscription.status in ACTIVE_STATUSES
        and subscription.current_period_end > now_utc()
    )


def require_active_access(db: Session, user_id: str) -> None:
    if not has_active_access(db, user_id):
        raise HTTPException(
            status_code=402,
            detail={
                "error": "subscription_required",
                "message": "An active subscription is required.",
                "upgrade_url": "/pricing",
            },
        )


def audit(
    db: Session,
    *,
    user_id: str | None,
    action: str,
    entity_type: str,
    entity_id: str | None,
    metadata: dict[str, Any] | None = None,
) -> None:
    db.add(
        BillingAuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_json=metadata,
            created_at=now_utc(),
        )
    )


async def create_checkout(db: Session, *, user_id: str, email: str, plan_code: str) -> dict[str, Any]:
    plan = get_plan(db, plan_code)
    reference = f"MC-{secrets.token_hex(12)}"
    now = now_utc()

    customer = db.scalar(select(BillingCustomer).where(BillingCustomer.user_id == user_id))
    if not customer:
        customer = BillingCustomer(
            user_id=user_id,
            email=email,
            created_at=now,
            updated_at=now,
        )
        db.add(customer)
    else:
        customer.email = email
        customer.updated_at = now

    payment = BillingPayment(
        user_id=user_id,
        plan_code=plan.code,
        reference=reference,
        amount_subunits=plan.amount_subunits,
        currency=plan.currency,
        status="pending",
        created_at=now,
        updated_at=now,
    )
    db.add(payment)
    db.flush()

    metadata = {
        "user_id": user_id,
        "plan_code": plan.code,
        "payment_id": payment.id,
        "access_days": plan.access_days,
    }

    payload: dict[str, Any] = {
        "email": email,
        "amount": str(plan.amount_subunits),
        "currency": plan.currency,
        "reference": reference,
        "callback_url": f"{settings.frontend_url}/billing/callback",
        "metadata": json.dumps(metadata),
    }

    if plan.is_recurring:
        if not settings.premium_plan_code:
            raise HTTPException(status_code=503, detail="PAYSTACK_PREMIUM_PLAN_CODE is not configured.")
        payload["plan"] = settings.premium_plan_code

    checkout = await paystack.initialize_transaction(payload)
    audit(
        db,
        user_id=user_id,
        action="checkout_initialized",
        entity_type="payment",
        entity_id=payment.id,
        metadata={"plan_code": plan.code, "reference": reference},
    )
    db.commit()

    return {
        "authorization_url": checkout["authorization_url"],
        "access_code": checkout["access_code"],
        "reference": checkout["reference"],
        "plan": serialize_plan(plan),
    }


async def verify_and_fulfil(db: Session, *, user_id: str, reference: str) -> dict[str, Any]:
    payment = db.scalar(
        select(BillingPayment).where(
            BillingPayment.reference == reference,
            BillingPayment.user_id == user_id,
        )
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Payment reference not found.")

    if payment.status == "success":
        subscription = get_current_subscription(db, user_id)
        return {
            "payment": serialize_payment(payment),
            "subscription": serialize_subscription(subscription),
            "already_processed": True,
        }

    transaction = await paystack.verify_transaction(reference)

    if transaction.get("status") != "success":
        raise HTTPException(status_code=400, detail="Payment has not completed successfully.")
    if int(transaction.get("amount", -1)) != payment.amount_subunits:
        raise HTTPException(status_code=400, detail="Payment amount mismatch.")
    if transaction.get("currency") != payment.currency:
        raise HTTPException(status_code=400, detail="Payment currency mismatch.")
    if transaction.get("reference") != reference:
        raise HTTPException(status_code=400, detail="Payment reference mismatch.")

    payment.status = "success"
    payment.paystack_transaction_id = str(transaction.get("id"))
    payment.channel = transaction.get("channel")
    payment.paid_at = parse_datetime(transaction.get("paid_at"))
    payment.verified_at = now_utc()
    payment.gateway_response = transaction
    payment.updated_at = now_utc()

    authorization = transaction.get("authorization") or {}
    payment.authorization_last4 = authorization.get("last4")
    payment.authorization_brand = authorization.get("brand") or authorization.get("card_type")

    customer_data = transaction.get("customer") or {}
    customer = db.scalar(select(BillingCustomer).where(BillingCustomer.user_id == user_id))
    if customer:
        customer.paystack_customer_code = customer_data.get("customer_code")
        customer.updated_at = now_utc()

    subscription_data = transaction.get("subscription") or {}
    subscription = activate_subscription(
        db,
        user_id=user_id,
        plan_code=payment.plan_code,
        customer_code=customer_data.get("customer_code"),
        subscription_code=subscription_data.get("subscription_code")
        if isinstance(subscription_data, dict)
        else None,
        email_token=subscription_data.get("email_token")
        if isinstance(subscription_data, dict)
        else None,
    )

    audit(
        db,
        user_id=user_id,
        action="payment_verified",
        entity_type="payment",
        entity_id=payment.id,
        metadata={"reference": reference, "plan_code": payment.plan_code},
    )
    db.commit()

    return {
        "payment": serialize_payment(payment),
        "subscription": serialize_subscription(subscription),
        "already_processed": False,
    }


def activate_subscription(
    db: Session,
    *,
    user_id: str,
    plan_code: str,
    customer_code: str | None,
    subscription_code: str | None,
    email_token: str | None,
) -> BillingSubscription:
    plan = get_plan(db, plan_code)
    now = now_utc()

    previous = get_current_subscription(db, user_id)
    if previous and previous.status in ACTIVE_STATUSES:
        previous.status = "expired"
        previous.expired_at = now
        previous.updated_at = now

    subscription = BillingSubscription(
        user_id=user_id,
        plan_code=plan.code,
        status="active",
        paystack_customer_code=customer_code,
        paystack_subscription_code=subscription_code,
        paystack_email_token=email_token,
        current_period_start=now,
        current_period_end=now + timedelta(days=plan.access_days),
        cancel_at_period_end=False,
        created_at=now,
        updated_at=now,
    )
    db.add(subscription)
    db.flush()
    return subscription


async def cancel_renewal(db: Session, *, user_id: str, reason: str | None) -> BillingSubscription:
    subscription = get_current_subscription(db, user_id)
    if not subscription or subscription.status not in ACTIVE_STATUSES:
        raise HTTPException(status_code=404, detail="No active subscription found.")

    if subscription.paystack_subscription_code and subscription.paystack_email_token:
        await paystack.disable_subscription(
            subscription.paystack_subscription_code,
            subscription.paystack_email_token,
        )

    subscription.status = "non_renewing"
    subscription.cancel_at_period_end = True
    subscription.cancelled_at = now_utc()
    subscription.updated_at = now_utc()

    audit(
        db,
        user_id=user_id,
        action="renewal_cancelled",
        entity_type="subscription",
        entity_id=subscription.id,
        metadata={"reason": reason},
    )
    db.commit()
    return subscription


async def reactivate(db: Session, *, user_id: str) -> BillingSubscription:
    subscription = get_current_subscription(db, user_id)
    if not subscription or not subscription.paystack_subscription_code or not subscription.paystack_email_token:
        raise HTTPException(status_code=400, detail="Subscription cannot be reactivated.")

    await paystack.enable_subscription(
        subscription.paystack_subscription_code,
        subscription.paystack_email_token,
    )
    subscription.status = "active"
    subscription.cancel_at_period_end = False
    subscription.cancelled_at = None
    subscription.updated_at = now_utc()
    audit(db, user_id=user_id, action="subscription_reactivated", entity_type="subscription", entity_id=subscription.id)
    db.commit()
    return subscription


async def get_management_link(db: Session, *, user_id: str) -> str:
    subscription = get_current_subscription(db, user_id)
    if not subscription or not subscription.paystack_subscription_code:
        raise HTTPException(status_code=404, detail="No recurring subscription found.")
    data = await paystack.management_link(subscription.paystack_subscription_code)
    return data["link"]


def expire_due_subscriptions(db: Session) -> int:
    now = now_utc()
    rows = db.scalars(
        select(BillingSubscription).where(
            BillingSubscription.status.in_(tuple(ACTIVE_STATUSES)),
            BillingSubscription.current_period_end <= now,
        )
    ).all()

    for row in rows:
        row.status = "expired"
        row.expired_at = now
        row.updated_at = now
        audit(db, user_id=row.user_id, action="subscription_expired", entity_type="subscription", entity_id=row.id)

    db.commit()
    return len(rows)


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def serialize_plan(plan: BillingPlan) -> dict[str, Any]:
    return {
        "code": plan.code,
        "name": plan.name,
        "description": plan.description,
        "amount_subunits": plan.amount_subunits,
        "amount": f"{plan.amount_subunits / 100:.2f}",
        "currency": plan.currency,
        "access_days": plan.access_days,
        "is_recurring": plan.is_recurring,
    }


def serialize_payment(payment: BillingPayment | None) -> dict[str, Any] | None:
    if not payment:
        return None
    return {
        "id": payment.id,
        "reference": payment.reference,
        "plan_code": payment.plan_code,
        "amount_subunits": payment.amount_subunits,
        "currency": payment.currency,
        "status": payment.status,
        "channel": payment.channel,
        "authorization_last4": payment.authorization_last4,
        "authorization_brand": payment.authorization_brand,
        "paid_at": payment.paid_at,
        "created_at": payment.created_at,
    }


def serialize_subscription(subscription: BillingSubscription | None) -> dict[str, Any] | None:
    if not subscription:
        return None
    return {
        "id": subscription.id,
        "plan_code": subscription.plan_code,
        "status": subscription.status,
        "current_period_start": subscription.current_period_start,
        "current_period_end": subscription.current_period_end,
        "cancel_at_period_end": subscription.cancel_at_period_end,
        "cancelled_at": subscription.cancelled_at,
    }
