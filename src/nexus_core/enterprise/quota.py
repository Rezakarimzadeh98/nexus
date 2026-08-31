"""Tenant quota checks for ingest volume."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from nexus_core.db.models import ObservationRow, TenantRow
from nexus_core.ids import utc_now


class QuotaExceeded(Exception):
    def __init__(self, slug: str, used: int, limit: int) -> None:
        super().__init__(f"tenant {slug} ingest quota exceeded ({used}/{limit})")
        self.slug = slug
        self.used = used
        self.limit = limit


def monthly_observation_count(session: Session, tenant_id: UUID) -> int:
    start = utc_now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return int(
        session.execute(
            select(func.count())
            .select_from(ObservationRow)
            .where(ObservationRow.tenant_id == tenant_id, ObservationRow.fetched_at >= start)
        ).scalar_one()
    )


def assert_ingest_quota(session: Session, tenant_id: UUID, *, incoming: int = 1) -> None:
    tenant = session.get(TenantRow, tenant_id)
    if tenant is None:
        return
    used = monthly_observation_count(session, tenant_id)
    limit = tenant.monthly_ingest_quota
    if used + incoming > limit:
        raise QuotaExceeded(tenant.slug, used, limit)


def days_until_month_reset() -> int:
    now = utc_now()
    if now.month == 12:
        nxt = now.replace(year=now.year + 1, month=1, day=1)
    else:
        nxt = now.replace(month=now.month + 1, day=1)
    return max(1, (nxt.date() - now.date()).days)
