from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CNC Master Cloud"
    environment: str = "development"
    log_level: str = "INFO"

    bot_token: str = ""
    api_base_url: str = "http://api:8000"
    database_url: str = "postgresql+asyncpg://cnc:cnc@db:5432/cnc_master"
    redis_url: str = "redis://redis:6379/0"
    admin_key: str = "change-me-now"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
