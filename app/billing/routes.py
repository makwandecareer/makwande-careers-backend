from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, HttpUrl

from app.config import settings
from app.database import get_connection
from app.dependencies import get_current_user

router = APIRouter(prefix="/billing", tags=["Billing & Paystack"])

PLANS = {
    "trial_14_days": {
        "name": "14-Day Unlimited CV Trial",
        "amount": 4500,
        "currency": "ZAR",
        "duration_days": 14,
    },
    "premium_30_days": {
        "name": "30-Day Premium",
        "amount": 30000,
        "currency": "ZAR",
        "duration_days": 30,
    },
}


class InitializePaymentRequest(BaseModel):
    plan: Literal["trial_14_days", "premium_30_days"]
    callback_url: HttpUrl | None = None


def _paystack_request(method: str, path: str, payload: dict | None = None) -> dict:
    secret_key = settings.paystack_secret_key.strip()
    if not secret_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PAYSTACK_SECRET_KEY is not configured",
        )

    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"https://api.paystack.co{path}",
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            message = json.loads(exc.read().decode("utf-8")).get("message")
        except Exception:
            message = "Paystack rejected the request"
        raise HTTPException(status_code=exc.code, detail=message) from exc
    except urllib.error.URLError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not connect to Paystack",
        ) from exc


def _store_pending_transaction(
    *, reference: str, user_id: Any, plan_key: str, email: str
) -> None:
    plan = PLANS[plan_key]
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO payment_transactions (
                    reference, user_id, email, plan_key, expected_amount,
                    currency, status, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, 'pending', NOW(), NOW())
                ON CONFLICT (reference) DO NOTHING
                """,
                (
                    reference,
                    user_id,
                    email,
                    plan_key,
                    plan["amount"],
                    plan["currency"],
                ),
            )
        connection.commit()


def _mark_transaction_failed(reference: str, status_value: str, raw_event: dict) -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE payment_transactions
                SET status = %s, raw_event = %s::jsonb, updated_at = NOW()
                WHERE reference = %s AND status <> 'success'
                """,
                (status_value, json.dumps(raw_event), reference),
            )
        connection.commit()


def _activate_subscription(reference: str, verified_data: dict) -> None:
    """Idempotently mark a transaction paid and grant/extend access."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT reference, user_id, plan_key, expected_amount, currency, status
                FROM payment_transactions
                WHERE reference = %s
                FOR UPDATE
                """,
                (reference,),
            )
            transaction = cursor.fetchone()

            if transaction is None:
                return

            if transaction["status"] == "success":
                return

            actual_status = verified_data.get("status")
            actual_amount = verified_data.get("amount")
            actual_currency = verified_data.get("currency")

            if actual_status != "success":
                cursor.execute(
                    """
                    UPDATE payment_transactions
                    SET status = %s, raw_event = %s::jsonb, updated_at = NOW()
                    WHERE reference = %s
                    """,
                    (
                        str(actual_status or "failed"),
                        json.dumps(verified_data),
                        reference,
                    ),
                )
                connection.commit()
                return

            if actual_amount != transaction["expected_amount"]:
                cursor.execute(
                    """
                    UPDATE payment_transactions
                    SET status = 'amount_mismatch', raw_event = %s::jsonb, updated_at = NOW()
                    WHERE reference = %s
                    """,
                    (json.dumps(verified_data), reference),
                )
                connection.commit()
                return

            if actual_currency != transaction["currency"]:
                cursor.execute(
                    """
                    UPDATE payment_transactions
                    SET status = 'currency_mismatch', raw_event = %s::jsonb, updated_at = NOW()
                    WHERE reference = %s
                    """,
                    (json.dumps(verified_data), reference),
                )
                connection.commit()
                return

            plan_key = transaction["plan_key"]
            plan = PLANS.get(plan_key)
            if plan is None:
                return

            now = datetime.now(timezone.utc)
            cursor.execute(
                "SELECT expires_at FROM subscriptions WHERE user_id = %s FOR UPDATE",
                (transaction["user_id"],),
            )
            current_subscription = cursor.fetchone()

            starts_at = now
            extension_base = now
            if current_subscription and current_subscription["expires_at"]:
                current_expiry = current_subscription["expires_at"]
                if current_expiry > now:
                    extension_base = current_expiry

            expires_at = extension_base + timedelta(days=plan["duration_days"])
            paid_at_raw = verified_data.get("paid_at") or verified_data.get("paidAt")
            paystack_id = verified_data.get("id")

            cursor.execute(
                """
                UPDATE payment_transactions
                SET status = 'success', paystack_transaction_id = %s,
                    paid_at = COALESCE(%s::timestamptz, NOW()),
                    raw_event = %s::jsonb, updated_at = NOW()
                WHERE reference = %s
                """,
                (paystack_id, paid_at_raw, json.dumps(verified_data), reference),
            )

            cursor.execute(
                """
                INSERT INTO subscriptions (
                    user_id, plan_key, status, starts_at, expires_at,
                    payment_reference, updated_at
                )
                VALUES (%s, %s, 'active', %s, %s, %s, NOW())
                ON CONFLICT (user_id) DO UPDATE SET
                    plan_key = EXCLUDED.plan_key,
                    status = 'active',
                    starts_at = EXCLUDED.starts_at,
                    expires_at = EXCLUDED.expires_at,
                    payment_reference = EXCLUDED.payment_reference,
                    updated_at = NOW()
                """,
                (
                    transaction["user_id"],
                    plan_key,
                    starts_at,
                    expires_at,
                    reference,
                ),
            )
        connection.commit()


def _process_charge_success(reference: str) -> None:
    """Verify with Paystack, then fulfill the plan. Runs after webhook response."""
    try:
        encoded_reference = urllib.parse.quote(reference, safe="")
        result = _paystack_request("GET", f"/transaction/verify/{encoded_reference}")
        data = result.get("data", {})
        _activate_subscription(reference, data)
    except Exception:
        # Paystack will retry failed webhook deliveries. Avoid marking successful
        # transactions as paid unless server-side verification succeeds.
        return


@router.get("/plans")
def list_plans() -> dict:
    return {"plans": PLANS}


@router.get("/status")
def billing_status() -> dict:
    paystack = settings.integration_status()["paystack"]
    return {"provider": "paystack", **paystack}


@router.get("/subscription")
def subscription_status(user: dict = Depends(get_current_user)) -> dict:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT plan_key, status, starts_at, expires_at, payment_reference
                FROM subscriptions
                WHERE user_id = %s
                """,
                (user["id"],),
            )
            subscription = cursor.fetchone()

    if not subscription:
        return {"active": False, "subscription": None}

    now = datetime.now(timezone.utc)
    active = subscription["status"] == "active" and subscription["expires_at"] > now
    return {"active": active, "subscription": subscription}


@router.post("/initialize")
def initialize_payment(
    request: InitializePaymentRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    email = user.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="The user account has no email address")

    plan = PLANS[request.plan]
    reference = f"mk-{user.get('id', 'user')}-{secrets.token_hex(8)}"
    _store_pending_transaction(
        reference=reference,
        user_id=user["id"],
        plan_key=request.plan,
        email=email,
    )

    payload = {
        "email": email,
        "amount": plan["amount"],
        "currency": plan["currency"],
        "reference": reference,
        "metadata": {
            "user_id": str(user.get("id", "")),
            "plan": request.plan,
            "duration_days": plan["duration_days"],
        },
    }
    if request.callback_url is not None:
        payload["callback_url"] = str(request.callback_url)

    try:
        result = _paystack_request("POST", "/transaction/initialize", payload)
    except HTTPException:
        _mark_transaction_failed(reference, "initialization_failed", payload)
        raise

    return {
        "plan": request.plan,
        "reference": reference,
        "payment": result.get("data", {}),
    }


@router.post("/webhook", include_in_schema=True)
async def paystack_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_paystack_signature: str | None = Header(default=None),
) -> dict:
    """Receive and authenticate Paystack events. No user JWT is required."""
    secret_key = settings.paystack_secret_key.strip()
    if not secret_key:
        raise HTTPException(status_code=503, detail="Paystack is not configured")

    raw_body = await request.body()
    expected_signature = hmac.new(
        secret_key.encode("utf-8"), raw_body, hashlib.sha512
    ).hexdigest()

    if not x_paystack_signature or not hmac.compare_digest(
        expected_signature, x_paystack_signature
    ):
        raise HTTPException(status_code=401, detail="Invalid Paystack signature")

    try:
        event = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid webhook payload") from exc

    event_name = event.get("event")
    data = event.get("data") or {}
    reference = data.get("reference")

    if event_name == "charge.success" and reference:
        # Return promptly; verify and fulfill after the 200 response is sent.
        background_tasks.add_task(_process_charge_success, str(reference))

    return {"received": True}


@router.get("/verify/{reference}")
def verify_payment(
    reference: str,
    user: dict = Depends(get_current_user),
) -> dict:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT user_id FROM payment_transactions WHERE reference = %s",
                (reference,),
            )
            transaction = cursor.fetchone()

    if transaction is None or transaction["user_id"] != user["id"]:
        raise HTTPException(status_code=404, detail="Payment reference not found")

    encoded_reference = urllib.parse.quote(reference, safe="")
    result = _paystack_request("GET", f"/transaction/verify/{encoded_reference}")
    data = result.get("data", {})
    _activate_subscription(reference, data)

    return {
        "reference": reference,
        "status": data.get("status"),
        "paid": data.get("status") == "success",
        "data": data,
    }
