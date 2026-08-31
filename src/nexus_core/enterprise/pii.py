"""PII handling helpers — redact before logs / exports when policy requires."""

from __future__ import annotations

import re
from typing import Any

_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{4}\b")


def redact_text(value: str) -> str:
    out = _EMAIL.sub("[REDACTED_EMAIL]", value)
    return _PHONE.sub("[REDACTED_PHONE]", out)


def redact_mapping(data: dict[str, Any], *, keys: set[str] | None = None) -> dict[str, Any]:
    sensitive = keys or {"email", "phone", "ssn", "password", "secret", "token"}
    out: dict[str, Any] = {}
    for k, v in data.items():
        if k.lower() in sensitive:
            out[k] = "[REDACTED]"
        elif isinstance(v, str):
            out[k] = redact_text(v)
        elif isinstance(v, dict):
            out[k] = redact_mapping(v, keys=sensitive)
        else:
            out[k] = v
    return out
