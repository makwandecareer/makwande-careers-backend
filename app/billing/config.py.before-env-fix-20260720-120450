from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class BillingSettings:
    database_url: str
    paystack_secret_key: str
    paystack_public_key: str
    premium_plan_code: str
    frontend_url: str
    webhook_secret: str
    cron_secret: str
    environment: str

    @classmethod
    def from_env(cls) -> "BillingSettings":
        database_url = os.getenv("DATABASE_URL", "").strip()
        if not database_url:
            raise RuntimeError("DATABASE_URL is required.")

        return cls(
            database_url=database_url,
            paystack_secret_key=os.getenv("PAYSTACK_SECRET_KEY", "").strip(),
            paystack_public_key=os.getenv("PAYSTACK_PUBLIC_KEY", "").strip(),
            premium_plan_code=os.getenv("PAYSTACK_PREMIUM_PLAN_CODE", "").strip(),
            frontend_url=os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/"),
            webhook_secret=os.getenv("PAYSTACK_WEBHOOK_SECRET", "").strip(),
            cron_secret=os.getenv("BILLING_CRON_SECRET", "").strip(),
            environment=os.getenv("ENVIRONMENT", "development").strip(),
        )


settings = BillingSettings.from_env()
