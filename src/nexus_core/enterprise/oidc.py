"""OIDC discovery + HS256 demo and JWKS/RS256 production validation."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from functools import lru_cache
from typing import Any, cast
from urllib.request import Request, urlopen

from nexus_core.config import get_settings

USER_AGENT = "NEXUS-OIDC/1.2 (+https://github.com/Rezakarimzadeh98/nexus)"


def oidc_discovery() -> dict[str, Any]:
    settings = get_settings()
    issuer = (settings.oidc_issuer or "https://sso.example.invalid/realms/nexus").rstrip("/")
    jwks = settings.oidc_jwks_uri or f"{issuer}/protocol/openid-connect/certs"
    return {
        "issuer": issuer,
        "authorization_endpoint": f"{issuer}/protocol/openid-connect/auth",
        "token_endpoint": f"{issuer}/protocol/openid-connect/token",
        "jwks_uri": jwks,
        "response_types_supported": ["code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256", "HS256"],
        "notes": (
            "Prefer JWKS/RS256 via NEXUS_OIDC_ISSUER (+ optional NEXUS_OIDC_JWKS_URI). "
            "HS256 demo uses NEXUS_OIDC_CLIENT_SECRET."
        ),
    }


def validate_oidc_bearer(token: str) -> dict[str, Any] | None:
    """Validate bearer JWT via JWKS/RS256 when issuer set, else HS256 demo secret."""
    if token.count(".") != 2:
        return None
    settings = get_settings()
    if settings.oidc_issuer or settings.oidc_jwks_uri:
        claims = _validate_rs256(token)
        if claims is not None:
            return claims
    if settings.oidc_client_secret:
        return _validate_hs256(token, settings.oidc_client_secret)
    return None


def _validate_hs256(token: str, secret: str) -> dict[str, Any] | None:
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
    payload = _decode_payload(payload_b64)
    if payload is None or not _claims_ok(payload):
        return None
    return payload


def _validate_rs256(token: str) -> dict[str, Any] | None:
    try:
        import jwt
    except ImportError:
        return None

    settings = get_settings()
    discovery = oidc_discovery()
    jwks_uri = settings.oidc_jwks_uri or str(discovery["jwks_uri"])
    try:
        client = _jwks_client(jwks_uri)
        signing_key = client.get_signing_key_from_jwt(token)
        decode_kwargs: dict[str, Any] = {
            "algorithms": ["RS256"],
            "options": {"require": ["exp", "sub"]},
        }
        if settings.oidc_audience:
            decode_kwargs["audience"] = settings.oidc_audience
        else:
            decode_kwargs["options"]["verify_aud"] = False
        if settings.oidc_issuer:
            decode_kwargs["issuer"] = settings.oidc_issuer.rstrip("/")
        payload = jwt.decode(token, signing_key.key, **decode_kwargs)
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


@lru_cache(maxsize=8)
def _jwks_client(jwks_uri: str) -> Any:
    from jwt import PyJWKClient

    return PyJWKClient(jwks_uri, cache_keys=True, lifespan=300, headers={"User-Agent": USER_AGENT})


def fetch_jwks(jwks_uri: str | None = None) -> dict[str, Any]:
    uri = jwks_uri or str(oidc_discovery()["jwks_uri"])
    req = Request(uri, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=20) as resp:  # noqa: S310 - configured IdP URL
        return cast(dict[str, Any], json.loads(resp.read().decode("utf-8")))


def clear_jwks_cache() -> None:
    _jwks_client.cache_clear()


def _decode_payload(payload_b64: str) -> dict[str, Any] | None:
    pad_p = "=" * (-len(payload_b64) % 4)
    try:
        return cast(dict[str, Any], json.loads(base64.urlsafe_b64decode(payload_b64 + pad_p)))
    except Exception:
        return None


def _claims_ok(payload: dict[str, Any]) -> bool:
    exp = payload.get("exp")
    if isinstance(exp, (int, float)) and time.time() > float(exp):
        return False
    aud = get_settings().oidc_audience
    if aud:
        token_aud = payload.get("aud")
        if isinstance(token_aud, list):
            if aud not in token_aud:
                return False
        elif token_aud != aud:
            return False
    return True
