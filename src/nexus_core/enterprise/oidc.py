"""OIDC discovery stub + HS256 JWT validation for enterprise SSO demos."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any, cast

from nexus_core.config import get_settings


def oidc_discovery() -> dict[str, Any]:
    settings = get_settings()
    issuer = settings.oidc_issuer or "https://sso.example.invalid/realms/nexus"
    return {
        "issuer": issuer,
        "authorization_endpoint": f"{issuer}/protocol/openid-connect/auth",
        "token_endpoint": f"{issuer}/protocol/openid-connect/token",
        "jwks_uri": f"{issuer}/protocol/openid-connect/certs",
        "response_types_supported": ["code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256", "HS256"],
        "notes": (
            "Wire a real IdP (Keycloak, Okta, Entra ID). "
            "Demo mode validates HS256 with NEXUS_OIDC_CLIENT_SECRET when set."
        ),
    }


def validate_oidc_bearer(token: str) -> dict[str, Any] | None:
    """Return claims if token is a valid HS256 JWT for configured secret; else None."""
    secret = get_settings().oidc_client_secret
    if not secret or token.count(".") != 2:
        return None
    header_b64, payload_b64, sig_b64 = token.split(".")
    signing_input = f"{header_b64}.{payload_b64}".encode()
    expected = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    pad = "=" * (-len(sig_b64) % 4)
    try:
        got = base64.urlsafe_b64decode(sig_b64 + pad)
    except Exception:
        return None
    if not hmac.compare_digest(expected, got):
        return None
    pad_p = "=" * (-len(payload_b64) % 4)
    try:
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + pad_p))
    except Exception:
        return None
    exp = payload.get("exp")
    if isinstance(exp, (int, float)) and time.time() > float(exp):
        return None
    aud = get_settings().oidc_audience
    if aud:
        token_aud = payload.get("aud")
        if isinstance(token_aud, list):
            if aud not in token_aud:
                return None
        elif token_aud != aud:
            return None
    return cast(dict[str, Any], payload)
