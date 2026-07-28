from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    app_name: str = Field(
        default="Makwande Careers API",
        validation_alias="APP_NAME",
    )
    environment: str = Field(
        default="development",
        validation_alias="ENVIRONMENT",
    )

    # Authentication
    jwt_secret: str = Field(
        validation_alias="JWT_SECRET",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        validation_alias="JWT_ALGORITHM",
    )
    access_token_minutes: int = Field(
        default=30,
        validation_alias="ACCESS_TOKEN_MINUTES",
    )

    # Database
    database_url: str = Field(
        validation_alias="DATABASE_URL",
    )

    # Public application URLs
    frontend_url: str = Field(
        default="http://localhost:3002",
        validation_alias="FRONTEND_URL",
    )
    backend_url: str = Field(
        default="http://127.0.0.1:8000",
        validation_alias="BACKEND_URL",
    )

    # CORS
    cors_origins: list[str] | str = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:3002",
        ],
        validation_alias="CORS_ALLOWED_ORIGINS",
    )

    # OpenAI
    openai_api_key: str = Field(
        default="",
        validation_alias="OPENAI_API_KEY",
    )
    openai_model: str = Field(
        default="gpt-5.4-mini",
        validation_alias="OPENAI_MODEL",
    )

    # Paystack
    paystack_secret_key: str = Field(
        default="",
        validation_alias="PAYSTACK_SECRET_KEY",
    )
    paystack_public_key: str = Field(
        default="",
        validation_alias="PAYSTACK_PUBLIC_KEY",
    )
    paystack_premium_plan_code: str = Field(
        default="",
        validation_alias="PAYSTACK_PREMIUM_PLAN_CODE",
    )
    paystack_trial_plan_code: str = Field(
        default="",
        validation_alias="PAYSTACK_TRIAL_PLAN_CODE",
    )
    paystack_callback_url: str = Field(
        default="",
        validation_alias="PAYSTACK_CALLBACK_URL",
    )
    paystack_base_url: str = Field(
        default="https://api.paystack.co",
        validation_alias="PAYSTACK_BASE_URL",
    )

    # Email / SMTP
    smtp_host: str = Field(
        default="",
        validation_alias="SMTP_HOST",
    )
    smtp_port: int = Field(
        default=587,
        validation_alias="SMTP_PORT",
    )
    smtp_username: str = Field(
        default="",
        validation_alias="SMTP_USERNAME",
    )
    smtp_password: str = Field(
        default="",
        validation_alias="SMTP_PASSWORD",
    )
    smtp_from_email: str = Field(
        default="",
        validation_alias="SMTP_FROM_EMAIL",
    )
    smtp_from_name: str = Field(
        default="Makwande Careers",
        validation_alias="SMTP_FROM_NAME",
    )
    smtp_use_tls: bool = Field(
        default=True,
        validation_alias="SMTP_USE_TLS",
    )

    # Administration
    admin_email: str = Field(
        default="",
        validation_alias="ADMIN_EMAIL",
    )
    billing_cron_secret: str = Field(
        default="",
        validation_alias="BILLING_CRON_SECRET",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value):
        if isinstance(value, str):
            return [
                origin.strip()
                for origin in value.split(",")
                if origin.strip()
            ]

        return value

    @field_validator(
        "frontend_url",
        "backend_url",
        mode="after",
    )
    @classmethod
    def remove_trailing_slash(cls, value: str) -> str:
        return value.strip().rstrip("/")

    def integration_status(self) -> dict:
        """Return safe diagnostics without exposing credentials."""

        smtp_configured = all(
            [
                self.smtp_host.strip(),
                self.smtp_from_email.strip(),
            ]
        )

        return {
            "openai": {
                "configured": bool(
                    self.openai_api_key.strip()
                ),
                "model": (
                    self.openai_model.strip()
                    or "gpt-5.4-mini"
                ),
            },
            "paystack": {
                "configured": bool(
                    self.paystack_secret_key.strip()
                ),
                "public_key_configured": bool(
                    self.paystack_public_key.strip()
                ),
            },
            "smtp": {
                "configured": smtp_configured,
                "host": self.smtp_host.strip(),
                "port": self.smtp_port,
                "from_email_configured": bool(
                    self.smtp_from_email.strip()
                ),
                "tls_enabled": self.smtp_use_tls,
            },
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()