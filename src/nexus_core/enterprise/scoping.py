"""Tenant scoping helpers for fact-table queries."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Select
from sqlalchemy.orm import Session

from nexus_core.db.models import TenantRow
from nexus_core.enterprise.tenancy import get_tenant_by_slug


def resolve_tenant_id(session: Session, slug: str | None) -> UUID | None:
    if not slug:
        return None
    tenant = get_tenant_by_slug(session, slug)
    return tenant.id if tenant else None


def apply_tenant_filter(
    stmt: Select[Any],
    *,
    column: Any,
    tenant_id: UUID | None,
) -> Select[Any]:
    if tenant_id is None:
        return stmt
    return stmt.where(column == tenant_id)


def tenant_exists(session: Session, tenant_id: UUID) -> bool:
    return session.get(TenantRow, tenant_id) is not None
