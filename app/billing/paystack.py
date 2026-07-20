from __future__ import annotations

import hashlib
import hmac
from typing import Any

import httpx
from fastapi import HTTPException

from app.billing.config import settings


class PaystackClient:
    base_url = "https://api.paystack.co"

    def _headers(self) -> dict[str, str]:
        if not settings.paystack_secret_key:
            raise HTTPException(status_code=503, detail="PAYSTACK_SECRET_KEY is not configured.")
        return {
            "Authorization": f"Bearer {settings.paystack_secret_key}",
            "Content-Type": "application/json",
        }

    async def initialize_transaction(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", "/transaction/initialize", payload)

    async def verify_transaction(self, reference: str) -> dict[str, Any]:
        return await self._request("GET", f"/transaction/verify/{reference}")

    async def fetch_subscription(self, code: str) -> dict[str, Any]:
        return await self._request("GET", f"/subscription/{code}")

    async def disable_subscription(self, code: str, token: str) -> dict[str, Any]:
        return await self._request("POST", "/subscription/disable", {"code": code, "token": token})

    async def enable_subscription(self, code: str, token: str) -> dict[str, Any]:
        return await self._request("POST", "/subscription/enable", {"code": code, "token": token})

    async def management_link(self, code: str) -> dict[str, Any]:
        return await self._request("GET", f"/subscription/{code}/manage/link")

    async def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
            response = await client.request(
                method,
                f"{self.base_url}{path}",
                headers=self._headers(),
                json=payload,
            )

        try:
            body = response.json()
        except ValueError as exc:
            raise HTTPException(status_code=502, detail="Invalid response from Paystack.") from exc

        if response.is_error or not body.get("status"):
            raise HTTPException(
                status_code=502,
                detail=body.get("message", "Paystack request failed."),
            )

        return body["data"]

    def verify_webhook(self, raw_body: bytes, signature: str | None) -> bool:
        if not signature or not settings.paystack_secret_key:
            return False
        digest = hmac.new(
            settings.paystack_secret_key.encode("utf-8"),
            raw_body,
            hashlib.sha512,
        ).hexdigest()
        return hmac.compare_digest(digest, signature)


paystack = PaystackClient()
