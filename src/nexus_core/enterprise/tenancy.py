"""Tenant isolation helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_core.db.models import MembershipRow, TenantRow
from nexus_core.ids import new_id, utc_now
from nexus_core.types import NexusModel


class Tenant(NexusModel):
    id: UUID = Field(default_factory=new_id)
    slug: str
    name: str
    region: str = "global"
    status: str = "active"
    monthly_ingest_quota: int = 100_000
    retention_days: int = 365
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


def create_tenant(session: Session, tenant: Tenant) -> Tenant:
    session.add(
        TenantRow(
            id=tenant.id,
            slug=tenant.slug.lower().strip(),
            name=tenant.name,
            region=tenant.region,
            status=tenant.status,
            monthly_ingest_quota=tenant.monthly_ingest_quota,
            retention_days=tenant.retention_days,
            created_at=tenant.created_at,
            metadata_json=tenant.metadata,
        )
    )
    return tenant


def get_tenant_by_slug(session: Session, slug: str) -> Tenant | None:
    row = session.execute(
        select(TenantRow).where(TenantRow.slug == slug.lower().strip())
    ).scalar_one_or_none()
    if row is None:
        return None
    return _from_row(row)


def list_tenants(session: Session, *, limit: int = 100) -> list[Tenant]:
    rows = session.execute(select(TenantRow).limit(limit)).scalars().all()
    return [_from_row(r) for r in rows]


def upsert_membership(
    session: Session,
    *,
    tenant_id: UUID,
    subject: str,
    role: str,
) -> UUID:
    mid = new_id()
    session.add(
        MembershipRow(
            id=mid,
            tenant_id=tenant_id,
            subject=subject,
            role=role,
            created_at=utc_now(),
        )
    )
    return mid


def membership_role(session: Session, *, tenant_id: UUID, subject: str) -> str | None:
    row = session.execute(
        select(MembershipRow)
        .where(MembershipRow.tenant_id == tenant_id, MembershipRow.subject == subject)
        .limit(1)
    ).scalar_one_or_none()
    return row.role if row else None


def _from_row(row: TenantRow) -> Tenant:
    return Tenant(
        id=row.id,
        slug=row.slug,
        name=row.name,
        region=row.region,
        status=row.status,
        monthly_ingest_quota=row.monthly_ingest_quota,
        retention_days=row.retention_days,
        created_at=row.created_at,
        metadata=row.metadata_json or {},
    )
