from __future__ import annotations

import json
import logging
import os
from typing import Any
from urllib.parse import quote

import httpx
from dotenv import load_dotenv


load_dotenv()


logger = logging.getLogger(__name__)

PAYSTACK_BASE_URL = os.getenv(
    "PAYSTACK_BASE_URL",
    "https://api.paystack.co",
).strip().rstrip("/")
REQUEST_TIMEOUT_SECONDS = 30.0


class PaystackConfigurationError(RuntimeError):
    """Raised when Paystack configuration is missing or invalid."""


class PaystackRequestError(RuntimeError):
    """Raised when Paystack rejects a request or cannot be reached."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_data: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


def get_paystack_secret_key() -> str:
    secret_key = os.getenv(
        "PAYSTACK_SECRET_KEY",
        "",
    ).strip()
    secret_key = secret_key.strip("'\"").strip()

    if not secret_key:
        raise PaystackConfigurationError(
            "PAYSTACK_SECRET_KEY is missing."
        )

    if not secret_key.startswith(
        ("sk_test_", "sk_live_")
    ):
        raise PaystackConfigurationError(
            "PAYSTACK_SECRET_KEY must start with "
            "'sk_test_' or 'sk_live_'."
        )

    return secret_key


def get_headers() -> dict[str, str]:
    return {
        "Authorization": (
            f"Bearer {get_paystack_secret_key()}"
        ),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def extract_error_message(
    response_data: Any,
    fallback: str,
) -> str:
    if isinstance(response_data, dict):
        message = response_data.get("message")

        if isinstance(message, str) and message.strip():
            return message.strip()

        detail = response_data.get("detail")

        if isinstance(detail, str) and detail.strip():
            return detail.strip()

    return fallback


async def initialize_transaction(
    *,
    email: str,
    amount: int,
    reference: str,
    callback_url: str,
    currency: str = "ZAR",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    clean_email = email.strip().lower()
    clean_reference = reference.strip()
    clean_callback_url = callback_url.strip()
    clean_currency = currency.strip().upper()

    if not clean_email:
        raise PaystackRequestError(
            "A customer email address is required."
        )

    if amount <= 0:
        raise PaystackRequestError(
            "The payment amount must be greater than zero."
        )

    if not clean_reference:
        raise PaystackRequestError(
            "A unique payment reference is required."
        )

    if not clean_callback_url.startswith(
        ("http://", "https://")
    ):
        raise PaystackRequestError(
            "The callback URL must be a complete URL."
        )

    payload: dict[str, Any] = {
        "email": clean_email,
        "amount": str(amount),
        "currency": clean_currency,
        "reference": clean_reference,
        "callback_url": clean_callback_url,
    }

    if metadata:
        payload["metadata"] = json.dumps(
            metadata,
            default=str,
        )

    try:
        async with httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT_SECONDS
        ) as client:
            response = await client.post(
                f"{PAYSTACK_BASE_URL}/transaction/initialize",
                headers=get_headers(),
                json=payload,
            )

    except httpx.TimeoutException as exc:
        raise PaystackRequestError(
            "Paystack timed out while creating checkout."
        ) from exc

    except httpx.RequestError as exc:
        raise PaystackRequestError(
            f"Could not connect to Paystack: {exc}"
        ) from exc

    try:
        response_data: Any = response.json()
    except ValueError:
        response_data = {
            "message": response.text
            or "Paystack returned an invalid response."
        }

    paystack_status = (
        response_data.get("status")
        if isinstance(response_data, dict)
        else None
    )

    if (
        response.status_code < 200
        or response.status_code >= 300
        or paystack_status is not True
    ):
        message = extract_error_message(
            response_data,
            "Paystack rejected the transaction request.",
        )

        logger.error(
            "Paystack initialization rejected. HTTP status=%s, message=%s",
            response.status_code,
            message,
        )

        raise PaystackRequestError(
            message,
            status_code=response.status_code,
            response_data=response_data,
        )

    data = response_data.get("data")

    if not isinstance(data, dict):
        raise PaystackRequestError(
            "Paystack did not return transaction data.",
            status_code=response.status_code,
            response_data=response_data,
        )

    authorization_url = data.get(
        "authorization_url"
    )

    if not isinstance(
        authorization_url,
        str,
    ) or not authorization_url.startswith(
        "https://"
    ):
        raise PaystackRequestError(
            "Paystack did not return a valid checkout URL.",
            status_code=response.status_code,
            response_data=response_data,
        )

    return data


async def verify_transaction(
    reference: str,
) -> dict[str, Any]:
    clean_reference = reference.strip()

    if not clean_reference:
        raise PaystackRequestError(
            "A transaction reference is required."
        )

    encoded_reference = quote(
        clean_reference,
        safe="",
    )

    try:
        async with httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT_SECONDS
        ) as client:
            response = await client.get(
                (
                    f"{PAYSTACK_BASE_URL}/transaction/"
                    f"verify/{encoded_reference}"
                ),
                headers=get_headers(),
            )

    except httpx.TimeoutException as exc:
        raise PaystackRequestError(
            "Paystack timed out while verifying payment."
        ) from exc

    except httpx.RequestError as exc:
        raise PaystackRequestError(
            f"Could not connect to Paystack: {exc}"
        ) from exc

    try:
        response_data: Any = response.json()
    except ValueError:
        response_data = {
            "message": response.text
            or "Paystack returned an invalid response."
        }

    paystack_status = (
        response_data.get("status")
        if isinstance(response_data, dict)
        else None
    )

    if (
        response.status_code < 200
        or response.status_code >= 300
        or paystack_status is not True
    ):
        message = extract_error_message(
            response_data,
            "Paystack rejected the verification request.",
        )

        logger.error(
            "Paystack verification rejected. HTTP status=%s, message=%s",
            response.status_code,
            message,
        )

        raise PaystackRequestError(
            message,
            status_code=response.status_code,
            response_data=response_data,
        )

    data = response_data.get("data")

    if not isinstance(data, dict):
        raise PaystackRequestError(
            "Paystack did not return verification data.",
            status_code=response.status_code,
            response_data=response_data,
        )

    return data
