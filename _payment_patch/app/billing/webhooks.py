from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.billing.models import BillingPayment, BillingSubscription, BillingWebhookEvent
from app.billing.service import audit, now_utc, parse_datetime


def event_key(event_type: str, data: dict[str, Any], raw_body: bytes) -> str:
    identity = (
        data.get("id")
        or data.get("reference")
        or data.get("subscription_code")
        or data.get("invoice_code")
        or hashlib.sha256(raw_body).hexdigest()
    )
    return f"{event_type}:{identity}"


def persist_event(
    db: Session,
    *,
    event_type: str,
    data: dict[str, Any],
    payload: dict[str, Any],
    raw_body: bytes,
) -> BillingWebhookEvent | None:
    key = event_key(event_type, data, raw_body)
    existing = db.scalar(select(BillingWebhookEvent).where(BillingWebhookEvent.event_key == key))
    if existing:
        return None

    event = BillingWebhookEvent(
        event_key=key,
        event_type=event_type,
        payload=payload,
        processed=False,
        received_at=now_utc(),
    )
    db.add(event)
    db.flush()
    return event


def process_event(db: Session, event: BillingWebhookEvent) -> None:
    event_type = event.event_type
    data = event.payload.get("data") or {}

    try:
        if event_type == "charge.success":
            _charge_success(db, data)
        elif event_type == "subscription.create":
            _subscription_create(db, data)
        elif event_type == "subscription.not_renew":
            _subscription_not_renew(db, data)
        elif event_type == "subscription.disable":
            _subscription_disable(db, data)
        elif event_type == "invoice.update":
            _invoice_update(db, data)
        elif event_type == "invoice.payment_failed":
            _invoice_failed(db, data)

        event.processed = True
        event.processed_at = now_utc()
        event.processing_error = None
        db.commit()
    except Exception as exc:
        event.processing_error = str(exc)[:2000]
        db.commit()
        raise


def _charge_success(db: Session, data: dict[str, Any]) -> None:
    reference = data.get("reference")
    if not reference:
        return

    payment = db.scalar(select(BillingPayment).where(BillingPayment.reference == reference))
    if not payment:
        return

    payment.status = "success"
    payment.paystack_transaction_id = str(data.get("id"))
    payment.channel = data.get("channel")
    payment.paid_at = parse_datetime(data.get("paid_at"))
    payment.gateway_response = data
    payment.updated_at = now_utc()


def _subscription_create(db: Session, data: dict[str, Any]) -> None:
    code = data.get("subscription_code")
    if not code:
        return

    customer = data.get("customer") or {}
    email_token = data.get("email_token")
    subscription = db.scalar(
        select(BillingSubscription)
        .where(BillingSubscription.paystack_customer_code == customer.get("customer_code"))
        .order_by(BillingSubscription.created_at.desc())
        .limit(1)
    )
    if subscription:
        subscription.paystack_subscription_code = code
        subscription.paystack_email_token = email_token
        subscription.status = "active"
        subscription.updated_at = now_utc()


def _subscription_not_renew(db: Session, data: dict[str, Any]) -> None:
    code = data.get("subscription_code")
    subscription = db.scalar(
        select(BillingSubscription).where(BillingSubscription.paystack_subscription_code == code)
    )
    if subscription:
        subscription.status = "non_renewing"
        subscription.cancel_at_period_end = True
        subscription.updated_at = now_utc()


def _subscription_disable(db: Session, data: dict[str, Any]) -> None:
    code = data.get("subscription_code")
    subscription = db.scalar(
        select(BillingSubscription).where(BillingSubscription.paystack_subscription_code == code)
    )
    if subscription:
        subscription.status = "expired"
        subscription.expired_at = now_utc()
        subscription.updated_at = now_utc()


def _invoice_update(db: Session, data: dict[str, Any]) -> None:
    subscription_data = data.get("subscription") or {}
    code = subscription_data.get("subscription_code")
    subscription = db.scalar(
        select(BillingSubscription).where(BillingSubscription.paystack_subscription_code == code)
    )
    if subscription and data.get("paid") is True:
        period_start = parse_datetime(data.get("period_start"))
        period_end = parse_datetime(data.get("period_end"))
        if period_start:
            subscription.current_period_start = period_start
        if period_end:
            subscription.current_period_end = period_end
        subscription.status = "active"
        subscription.updated_at = now_utc()


def _invoice_failed(db: Session, data: dict[str, Any]) -> None:
    subscription_data = data.get("subscription") or {}
    code = subscription_data.get("subscription_code")
    subscription = db.scalar(
        select(BillingSubscription).where(BillingSubscription.paystack_subscription_code == code)
    )
    if subscription:
        subscription.status = "attention"
        subscription.updated_at = now_utc()
