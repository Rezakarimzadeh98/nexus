from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4


def utc_now() -> datetime:
    """Timezone-aware UTC timestamp."""
    return datetime.now(tz=UTC)


def ensure_utc(value: datetime) -> datetime:
    """Normalize naive or aware datetimes to UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def new_id() -> UUID:
    return uuid4()
