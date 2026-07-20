from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class IntegrationSettings:
    openai_api_key: str
    openai_model: str
    paystack_secret_key: str
    paystack_public_key: str
    paystack_premium_plan_code: str
    frontend_url: str
    jwt_secret_key: str
    jwt_algorithm: str
    database_path: Path

    @classmethod
    def from_env(cls) -> "IntegrationSettings":
        raw = os.getenv("DATABASE_URL", "").strip()
        path = Path(raw.removeprefix("sqlite:///")) if raw.startswith("sqlite:///") else Path(os.getenv("MAKWANDE_DB_PATH", "makwande.db"))
        return cls(
            os.getenv("OPENAI_API_KEY", "").strip(),
            os.getenv("OPENAI_MODEL", "gpt-5-mini").strip(),
            os.getenv("PAYSTACK_SECRET_KEY", "").strip(),
            os.getenv("PAYSTACK_PUBLIC_KEY", "").strip(),
            os.getenv("PAYSTACK_PREMIUM_PLAN_CODE", "").strip(),
            os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/"),
            os.getenv("JWT_SECRET_KEY", os.getenv("SECRET_KEY", "")).strip(),
            os.getenv("JWT_ALGORITHM", "HS256").strip(),
            path,
        )

settings = IntegrationSettings.from_env()
