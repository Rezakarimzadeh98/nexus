"""Append-only audit log."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_core.db.models import AuditEventRow
from nexus_core.ids import new_id, utc_now
from nexus_core.types import NexusModel


class AuditEvent(NexusModel):
    id: UUID = Field(default_factory=new_id)
    tenant_id: UUID | None = None
    actor: str
    action: str
    resource: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    detail: dict[str, Any] = Field(default_factory=dict)


def record_audit(session: Session, event: AuditEvent) -> AuditEvent:
    session.add(
        AuditEventRow(
            id=event.id,
            tenant_id=event.tenant_id,
            actor=event.actor,
            action=event.action,
            resource=event.resource,
            created_at=event.created_at,
            detail=event.detail,
        )
    )
    return event


def list_audit(
    session: Session,
    *,
    tenant_id: UUID | None = None,
    limit: int = 50,
) -> list[AuditEvent]:
    q = select(AuditEventRow).order_by(AuditEventRow.created_at.desc()).limit(limit)
    if tenant_id is not None:
        q = q.where(AuditEventRow.tenant_id == tenant_id)
    rows = session.execute(q).scalars().all()
    return [
        AuditEvent(
            id=r.id,
            tenant_id=r.tenant_id,
            actor=r.actor,
            action=r.action,
            resource=r.resource,
            created_at=r.created_at,
            detail=r.detail or {},
        )
        for r in rows
    ]
