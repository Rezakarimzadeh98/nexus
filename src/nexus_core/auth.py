"""HTTP auth helpers for write paths and enterprise identity."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Annotated

from fastapi import Header, HTTPException, status

from nexus_core.config import get_settings
from nexus_core.enterprise.oidc import validate_oidc_bearer


@dataclass(frozen=True)
class AuthContext:
    subject: str
    via: str  # api_key | oidc | anonymous


def _extract_token(
    authorization: str | None,
    x_api_key: str | None,
) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    if x_api_key:
        return x_api_key.strip()
    return None


def require_api_key(
    authorization: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> AuthContext:
    """Validate API key and/or OIDC bearer when configured."""
    settings = get_settings()
    token = _extract_token(authorization, x_api_key)

    if not settings.api_key and not settings.oidc_client_secret:
        return AuthContext(subject="anonymous", via="anonymous")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if settings.api_key and secrets.compare_digest(token, settings.api_key):
        return AuthContext(subject="api-key", via="api_key")

    if settings.oidc_client_secret:
        claims = validate_oidc_bearer(token)
        if claims and claims.get("sub"):
            return AuthContext(subject=str(claims["sub"]), via="oidc")

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key",
        headers={"WWW-Authenticate": "Bearer"},
    )
