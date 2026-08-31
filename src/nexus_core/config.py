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
        description="Optional Redis URL (cache / future broker)",
    )
    api_key: str | None = Field(
        default=None,
        description="Bearer token required for write paths when set",
    )
    snapshot_path: str = Field(
        default="docs/live/status.json",
        description="Fallback live snapshot JSON path",
    )
    default_tenant_slug: str = Field(
        default="public",
        description="Default tenant slug when X-Nexus-Tenant omitted",
    )
    oidc_issuer: str | None = Field(
        default=None,
        description="OIDC issuer URL for SSO discovery",
    )
    oidc_jwks_uri: str | None = Field(
        default=None,
        description="Optional override for JWKS URI (defaults from issuer)",
    )
    oidc_audience: str | None = Field(
        default=None,
        description="Expected JWT audience",
    )
    oidc_client_secret: str | None = Field(
        default=None,
        description="HS256 demo secret for OIDC bearer validation",
    )
    slo_ingest_success_ratio: float = Field(
        default=0.95,
        description="Target successful ingest job ratio (SLO)",
    )
    secrets_backend: str = Field(
        default="env",
        description="env | file — how secrets are loaded (enterprise)",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
