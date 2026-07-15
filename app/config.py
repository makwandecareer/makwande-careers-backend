from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    app_name: str = 'Makwande Careers API'
    environment: str = 'development'
    jwt_secret: str
    access_token_minutes: int = 30
    database_url: str
    cors_origins: list[str] | str = ['http://localhost:3000']

    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_origins(cls, value):
        if isinstance(value, str):
            return [x.strip() for x in value.split(',') if x.strip()]
        return value

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
