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

    app_name: str = "Makwande Careers API"
    environment: str = "development"
    jwt_secret: str
    access_token_minutes: int = 30
    database_url: str
    cors_origins: list[str] | str = ["http://localhost:3000"]

    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-5.4-mini", validation_alias="OPENAI_MODEL")
    paystack_secret_key: str = Field(default="", validation_alias="PAYSTACK_SECRET_KEY")
    paystack_public_key: str = Field(default="", validation_alias="PAYSTACK_PUBLIC_KEY")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value):
        if isinstance(value, str):
            return [x.strip() for x in value.split(",") if x.strip()]
        return value

    def integration_status(self) -> dict:
        """Return safe integration diagnostics without exposing secrets."""
        return {
            "openai": {
                "configured": bool(self.openai_api_key.strip()),
                "model": self.openai_model.strip() or "gpt-5.4-mini",
            },
            "paystack": {
                "configured": bool(self.paystack_secret_key.strip()),
                "public_key_configured": bool(self.paystack_public_key.strip()),
            },
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
