from __future__ import annotations

import os
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from psycopg.types.json import Jsonb

from app.database import get_connection
from app.dependencies import get_current_user
from app.services.paystack_service import (
    PaystackConfigurationError,
    PaystackRequestError,
    initialize_transaction,
    verify_transaction,
)


router = APIRouter(
    prefix="/billing",
    tags=["Billing & Paystack"],
)


PLANS: dict[str, dict[str, Any]] = {
    "trial_14_day": {
        "name": "14-Day Unlimited CV Trial",
        "amount": 4500,
        "display_amount": 45,
        "currency": "ZAR",
        "duration_days": 14,
    },
    "premium_30_day": {
        "name": "30-Day Premium",
        "amount": 30000,
        "display_amount": 300,
        "currency": "ZAR",
        "duration_days": 30,
    },
}


PLAN_ALIASES = {
    "trial_14_days": "trial_14_day",
    "premium_30_days": "premium_30_day",
}


class InitializePaymentRequest(BaseModel):
    plan: Literal[
        "trial_14_day",
        "premium_30_day",
        "trial_14_days",
        "premium_30_days",
    ]
    callback_url: str | None = None


def normalize_plan_code(plan_code: str) -> str:
    normalized = PLAN_ALIASES.get(plan_code, plan_code)

    if normalized not in PLANS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subscription plan.",
        )

    return normalized


def get_default_callback_url() -> str:
    frontend_url = os.getenv(
        "FRONTEND_URL",
        "http://localhost:3002",
    ).rstrip("/")

    return f"{frontend_url}/payment/callback"


def serialize_datetime(value: Any) -> str | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.isoformat()

    return str(value)


def expire_old_subscriptions(user_id: str) -> None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE subscriptions
                SET
                    status = 'expired',
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
                  AND status = 'active'
                  AND expires_at <= CURRENT_TIMESTAMP
                """,
                (user_id,),
            )

        connection.commit()


def get_active_subscription(user_id: str) -> dict | None:
    expire_old_subscriptions(user_id)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    user_id,
                    plan_key,
                    status,
                    starts_at,
                    expires_at,
                    payment_reference,
                    updated_at
                FROM subscriptions
                WHERE user_id = %s
                  AND status = 'active'
                  AND starts_at <= CURRENT_TIMESTAMP
                  AND expires_at > CURRENT_TIMESTAMP
                ORDER BY expires_at DESC
                LIMIT 1
                """,
                (user_id,),
            )

            return cursor.fetchone()


def get_latest_subscription(user_id: str) -> dict | None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    user_id,
                    plan_key,
                    status,
                    starts_at,
                    expires_at,
                    payment_reference,
                    updated_at
                FROM subscriptions
                WHERE user_id = %s
                ORDER BY updated_at DESC, expires_at DESC
                LIMIT 1
                """,
                (user_id,),
            )

            return cursor.fetchone()


def has_subscription_history(user_id: str) -> bool:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM subscriptions
                    WHERE user_id = %s
                ) AS has_history
                """,
                (user_id,),
            )

            result = cursor.fetchone()

    return bool(result and result["has_history"])


def has_used_trial(user_id: str) -> bool:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM subscriptions
                    WHERE user_id = %s
                      AND plan_key IN (
                          'trial_14_day',
                          'trial_14_days'
                      )
                ) AS trial_used
                """,
                (user_id,),
            )

            result = cursor.fetchone()

    return bool(result and result["trial_used"])


def build_subscription_response(
    subscription: dict | None,
) -> dict[str, Any]:
    if subscription is None:
        return {
            "has_access": False,
            "subscription": None,
        }

    plan_code = normalize_plan_code(
        str(subscription["plan_key"])
    )
    plan = PLANS[plan_code]

    return {
        "has_access": True,
        "subscription": {
            "plan_code": plan_code,
            "plan_key": plan_code,
            "name": plan["name"],
            "amount": plan["amount"],
            "display_amount": plan["display_amount"],
            "currency": plan["currency"],
            "duration_days": plan["duration_days"],
            "status": subscription["status"],
            "starts_at": serialize_datetime(
                subscription["starts_at"]
            ),
            "expires_at": serialize_datetime(
                subscription["expires_at"]
            ),
            "payment_reference": subscription[
                "payment_reference"
            ],
        },
    }


def get_plan_code_from_payment(payment_record: dict) -> str:
    plan_key = str(payment_record.get("plan_key") or "")

    if plan_key:
        return normalize_plan_code(plan_key)

    amount = int(payment_record["expected_amount"])

    for code, plan in PLANS.items():
        if int(plan["amount"]) == amount:
            return code

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unable to determine the subscription plan.",
    )


@router.get("/plans")
def list_plans() -> dict[str, Any]:
    return {
        "plans": [
            {
                "code": code,
                "name": plan["name"],
                "amount": plan["amount"],
                "display_amount": plan["display_amount"],
                "currency": plan["currency"],
                "duration_days": plan["duration_days"],
            }
            for code, plan in PLANS.items()
        ]
    }


@router.get("/status")
def billing_status(
    user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    user_id = str(user["id"])

    subscription = get_active_subscription(user_id)
    latest_subscription = get_latest_subscription(user_id)
    trial_used = has_used_trial(user_id)
    history_exists = latest_subscription is not None

    if subscription is not None:
        recommended_plan = normalize_plan_code(
            str(subscription["plan_key"])
        )
    elif history_exists:
        recommended_plan = "premium_30_day"
    else:
        recommended_plan = "trial_14_day"

    response = {
        "provider": "paystack",
        "user_id": user_id,
        "trial_available": not history_exists,
        "trial_used": trial_used,
        "recommended_plan": recommended_plan,
        **build_subscription_response(subscription),
    }

    if subscription is None and latest_subscription is not None:
        response["latest_subscription"] = {
            "plan_code": normalize_plan_code(
                str(latest_subscription["plan_key"])
            ),
            "status": latest_subscription["status"],
            "starts_at": serialize_datetime(
                latest_subscription["starts_at"]
            ),
            "expires_at": serialize_datetime(
                latest_subscription["expires_at"]
            ),
            "payment_reference": latest_subscription[
                "payment_reference"
            ],
        }

    return response


@router.post("/initialize")
async def initialize_payment(
    request: InitializePaymentRequest,
    user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    user_id = str(user["id"])
    email = str(user.get("email") or "").strip().lower()

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user account has no email address.",
        )

    plan_code = normalize_plan_code(request.plan)
    plan = PLANS[plan_code]

    if plan_code == "trial_14_day":
        if has_subscription_history(user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "TRIAL_NOT_AVAILABLE",
                    "message": (
                        "The R45 introductory trial is only "
                        "available for the first subscription. "
                        "Please select the R300 Premium plan."
                    ),
                    "required_plan": "premium_30_day",
                },
            )

    reference = (
        f"mk-{user_id[:8]}-"
        f"{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-"
        f"{secrets.token_hex(5)}"
    )

    callback_url = (
        request.callback_url.strip()
        if request.callback_url
        else get_default_callback_url()
    )

    if not callback_url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The callback URL must be a complete HTTP or HTTPS URL.",
        )

    try:
        payment = await initialize_transaction(
            email=email,
            amount=plan["amount"],
            reference=reference,
            callback_url=callback_url,
            currency=plan["currency"],
            metadata={
                "user_id": user_id,
                "plan_code": plan_code,
                "duration_days": plan["duration_days"],
            },
        )

    except PaystackConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    except PaystackRequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    raw_event = {
        "plan_code": plan_code,
        "duration_days": plan["duration_days"],
        "initialization": payment,
    }

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO payment_transactions (
                        reference,
                        user_id,
                        email,
                        plan_key,
                        expected_amount,
                        currency,
                        status,
                        paystack_transaction_id,
                        paid_at,
                        raw_event,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        'pending',
                        NULL,
                        NULL,
                        %s,
                        CURRENT_TIMESTAMP,
                        CURRENT_TIMESTAMP
                    )
                    """,
                    (
                        reference,
                        user_id,
                        email,
                        plan_code,
                        plan["amount"],
                        plan["currency"],
                        Jsonb(raw_event),
                    ),
                )

            connection.commit()

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Paystack checkout was created, but the payment "
                f"record could not be saved: {exc}"
            ),
        ) from exc

    return {
        "plan_code": plan_code,
        "reference": reference,
        "authorization_url": payment["authorization_url"],
        "access_code": payment.get("access_code"),
        "amount": plan["amount"],
        "display_amount": plan["display_amount"],
        "currency": plan["currency"],
    }


@router.get("/verify/{reference}")
async def verify_payment(
    reference: str,
    user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    user_id = str(user["id"])
    safe_reference = quote(reference, safe="")

    if safe_reference != reference:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment reference.",
        )

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM payment_transactions
                WHERE reference = %s
                LIMIT 1
                """,
                (reference,),
            )

            payment_record = cursor.fetchone()

    if payment_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment reference was not found.",
        )

    if str(payment_record["user_id"]) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This payment does not belong to your account.",
        )

    if payment_record["status"] == "success":
        subscription = get_active_subscription(user_id)

        return {
            "paid": True,
            "already_verified": True,
            "reference": reference,
            **build_subscription_response(subscription),
        }

    try:
        paystack_data = await verify_transaction(reference)

    except PaystackConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    except PaystackRequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    paystack_status = str(
        paystack_data.get("status") or ""
    ).lower()

    if paystack_status != "success":
        allowed_statuses = {
            "pending",
            "failed",
            "abandoned",
            "reversed",
        }

        stored_status = (
            paystack_status
            if paystack_status in allowed_statuses
            else "failed"
        )

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE payment_transactions
                    SET
                        status = %s,
                        raw_event = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE reference = %s
                    """,
                    (
                        stored_status,
                        Jsonb(paystack_data),
                        reference,
                    ),
                )

            connection.commit()

        return {
            "paid": False,
            "reference": reference,
            "status": paystack_status or "failed",
            "has_access": False,
        }

    expected_amount = int(payment_record["expected_amount"])
    returned_amount = int(paystack_data.get("amount") or 0)

    expected_currency = str(
        payment_record["currency"]
    ).upper()

    returned_currency = str(
        paystack_data.get("currency") or ""
    ).upper()

    returned_reference = str(
        paystack_data.get("reference") or ""
    )

    if returned_reference != reference:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Paystack returned a different payment reference.",
        )

    if returned_amount != expected_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The verified payment amount is incorrect.",
        )

    if returned_currency != expected_currency:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The verified payment currency is incorrect.",
        )

    customer = paystack_data.get("customer") or {}
    returned_email = str(
        customer.get("email") or ""
    ).strip().lower()

    account_email = str(
        user.get("email") or ""
    ).strip().lower()

    if returned_email and returned_email != account_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The Paystack customer email does not match "
                "your account."
            ),
        )

    plan_code = get_plan_code_from_payment(payment_record)
    plan = PLANS[plan_code]
    now = datetime.now(UTC)

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT *
                    FROM payment_transactions
                    WHERE reference = %s
                    FOR UPDATE
                    """,
                    (reference,),
                )

                locked_payment = cursor.fetchone()

                if locked_payment is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Payment record was not found.",
                    )

                if locked_payment["status"] == "success":
                    connection.commit()
                    subscription = get_active_subscription(user_id)

                    return {
                        "paid": True,
                        "already_verified": True,
                        "reference": reference,
                        **build_subscription_response(subscription),
                    }

                cursor.execute(
                    """
                    UPDATE subscriptions
                    SET
                        status = 'expired',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                      AND status = 'active'
                      AND expires_at <= CURRENT_TIMESTAMP
                    """,
                    (user_id,),
                )

                cursor.execute(
                    """
                    SELECT
                        user_id,
                        plan_key,
                        status,
                        starts_at,
                        expires_at,
                        payment_reference,
                        updated_at
                    FROM subscriptions
                    WHERE user_id = %s
                    ORDER BY updated_at DESC, expires_at DESC
                    LIMIT 1
                    FOR UPDATE
                    """,
                    (user_id,),
                )

                existing_subscription = cursor.fetchone()

                if plan_code == "trial_14_day":
                    if existing_subscription is not None:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail={
                                "code": "TRIAL_NOT_AVAILABLE",
                                "message": (
                                    "The R45 introductory trial has "
                                    "already been used. Please select "
                                    "the R300 Premium plan."
                                ),
                                "required_plan": "premium_30_day",
                            },
                        )

                if (
                    existing_subscription is not None
                    and existing_subscription["status"] == "active"
                    and existing_subscription["expires_at"] > now
                ):
                    current_expiry = existing_subscription["expires_at"]

                    if current_expiry.tzinfo is None:
                        current_expiry = current_expiry.replace(
                            tzinfo=UTC
                        )

                    starts_at = existing_subscription["starts_at"]
                    new_expiry = current_expiry + timedelta(
                        days=plan["duration_days"]
                    )
                else:
                    starts_at = now
                    new_expiry = now + timedelta(
                        days=plan["duration_days"]
                    )

                if existing_subscription is None:
                    cursor.execute(
                        """
                        INSERT INTO subscriptions (
                            user_id,
                            plan_key,
                            status,
                            starts_at,
                            expires_at,
                            payment_reference,
                            updated_at
                        )
                        VALUES (
                            %s,
                            %s,
                            'active',
                            %s,
                            %s,
                            %s,
                            CURRENT_TIMESTAMP
                        )
                        """,
                        (
                            user_id,
                            plan_code,
                            starts_at,
                            new_expiry,
                            reference,
                        ),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE subscriptions
                        SET
                            plan_key = %s,
                            status = 'active',
                            starts_at = %s,
                            expires_at = %s,
                            payment_reference = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = %s
                        """,
                        (
                            plan_code,
                            starts_at,
                            new_expiry,
                            reference,
                            user_id,
                        ),
                    )

                transaction_id = (
                    int(paystack_data["id"])
                    if paystack_data.get("id") is not None
                    else None
                )

                cursor.execute(
                    """
                    UPDATE payment_transactions
                    SET
                        status = 'success',
                        paystack_transaction_id = %s,
                        paid_at = CURRENT_TIMESTAMP,
                        raw_event = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE reference = %s
                    """,
                    (
                        transaction_id,
                        Jsonb(paystack_data),
                        reference,
                    ),
                )

            connection.commit()

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Payment succeeded, but subscription activation "
                f"failed: {exc}"
            ),
        ) from exc

    subscription = get_active_subscription(user_id)

    return {
        "paid": True,
        "already_verified": False,
        "reference": reference,
        **build_subscription_response(subscription),
    }