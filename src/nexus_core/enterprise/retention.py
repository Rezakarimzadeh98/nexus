"""Retention helpers — prune observations older than tenant policy."""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.orm import Session

from nexus_core.db.models import ObservationRow, TenantRow
from nexus_core.ids import utc_now


def apply_retention(session: Session, *, tenant_id: UUID | None = None) -> dict[str, int]:
    """Delete observations past retention using tenant_id column when set."""
    if tenant_id is not None:
        tenant = session.get(TenantRow, tenant_id)
        days = tenant.retention_days if tenant else 365
        cutoff = utc_now() - timedelta(days=days)
        result = session.execute(
            delete(ObservationRow).where(
                ObservationRow.tenant_id == tenant_id,
                ObservationRow.fetched_at < cutoff,
            )
        )
        deleted = int(getattr(result, "rowcount", 0) or 0)
    else:
        cutoff = utc_now() - timedelta(days=730)
        result = session.execute(delete(ObservationRow).where(ObservationRow.fetched_at < cutoff))
        deleted = int(getattr(result, "rowcount", 0) or 0)
    return {"deleted_observations": deleted}
