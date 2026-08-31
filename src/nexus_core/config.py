from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment / `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="NEXUS_",
        extra="ignore",
    )

    environment: str = Field(
        default="development",
        description="development | staging | production",
    )
    log_level: str = Field(default="INFO")
    database_url: str = Field(
        default="postgresql+psycopg://nexus:nexus@localhost:5432/nexus",
        description="SQLAlchemy URL (psycopg3 driver)",
    )
    redis_url: str | None = Field(
        default=None,
        description="Optional Redis URL for later phases",
    )
    api_key: str | None = Field(
        default=None,
        description="Bearer token required for write paths when set",
    )
    snapshot_path: str = Field(
        default="docs/live/status.json",
        description="Fallback live snapshot JSON path",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
