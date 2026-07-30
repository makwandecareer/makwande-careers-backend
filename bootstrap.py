from __future__ import annotations

import logging
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application configuration.
    Values are loaded from environment variables or a .env file.
    """

    APP_NAME: str = "Makwande Careers"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"

    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-5.5"

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


class ServiceContainer:
    """
    Simple dependency container.

    Register shared services here so they are created once and
    injected throughout the application.
    """

    def __init__(self):
        self.settings = get_settings()

        from app.services.ai_provider import AIProvider
        from app.services.background_task_service import background_tasks

        self.ai_provider = AIProvider()
        self.background_tasks = background_tasks


container = ServiceContainer()
