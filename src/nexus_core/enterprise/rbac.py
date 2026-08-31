"""Role-based access control for enterprise write/admin paths."""

from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    VIEWER = "viewer"
    OPERATOR = "operator"
    ADMIN = "admin"


_RANK = {
    Role.VIEWER: 1,
    Role.OPERATOR: 2,
    Role.ADMIN: 3,
}

_ACTION_MIN: dict[str, Role] = {
    "read": Role.VIEWER,
    "ingest": Role.OPERATOR,
    "detect": Role.OPERATOR,
    "jobs": Role.OPERATOR,
    "audit.read": Role.ADMIN,
    "tenant.write": Role.ADMIN,
    "membership.write": Role.ADMIN,
    "admin": Role.ADMIN,
}


def role_allows(role: str | Role, action: str) -> bool:
    try:
        r = Role(str(role).lower())
    except ValueError:
        return False
    needed = _ACTION_MIN.get(action, Role.ADMIN)
    return _RANK[r] >= _RANK[needed]
