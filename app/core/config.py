from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "OrderFlow API"
    environment: str = "development"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    database_url: str = "postgresql+psycopg://orderflow:orderflow@localhost:5432/orderflow"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: str = Field(default="local-development-only-change-me", min_length=16)
    jwt_access_token_minutes: int = 15
    jwt_refresh_token_days: int = 7
    frontend_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

