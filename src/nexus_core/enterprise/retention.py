"""Retention helpers — prune observations older than tenant policy."""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from nexus_core.db.models import ObservationRow, TenantRow
from nexus_core.ids import utc_now


def apply_retention(session: Session, *, tenant_id: UUID | None = None) -> dict[str, int]:
    """Delete observations past retention. Tenant-scoped via metadata.tenant_id when set."""
    deleted = 0
    if tenant_id is not None:
        tenant = session.get(TenantRow, tenant_id)
        days = tenant.retention_days if tenant else 365
        cutoff = utc_now() - timedelta(days=days)
        # Metadata filter for tenant isolation without rewriting all core tables.
        rows = session.execute(
            select(ObservationRow.id, ObservationRow.fetched_at, ObservationRow.metadata_json)
        ).all()
        ids = [
            r.id
            for r in rows
            if r.fetched_at < cutoff
            and (r.metadata_json or {}).get("tenant_id") == str(tenant_id)
        ]
        for oid in ids:
            session.execute(delete(ObservationRow).where(ObservationRow.id == oid))
        deleted = len(ids)
    else:
        # Global default: 730 days for unscoped rows
        cutoff = utc_now() - timedelta(days=730)
        result = session.execute(delete(ObservationRow).where(ObservationRow.fetched_at < cutoff))
        deleted = int(getattr(result, "rowcount", 0) or 0)
    return {"deleted_observations": deleted}
