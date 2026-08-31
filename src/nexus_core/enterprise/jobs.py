"""DB-backed job queue (horizontal workers claim rows). Redis optional later."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_core.db.models import JobRow
from nexus_core.ids import new_id, utc_now
from nexus_core.types import NexusModel


class JobRecord(NexusModel):
    id: UUID = Field(default_factory=new_id)
    tenant_id: UUID | None = None
    kind: str
    status: str = "queued"
    payload: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] | None = None
    created_at: datetime = Field(default_factory=utc_now)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None


def enqueue_job(session: Session, job: JobRecord) -> JobRecord:
    session.add(
        JobRow(
            id=job.id,
            tenant_id=job.tenant_id,
            kind=job.kind,
            status="queued",
            payload=job.payload,
            result=None,
            created_at=job.created_at,
            started_at=None,
            finished_at=None,
            error=None,
        )
    )
    return job


def claim_next_job(session: Session, *, kinds: list[str] | None = None) -> JobRecord | None:
    q = (
        select(JobRow)
        .where(JobRow.status == "queued")
        .order_by(JobRow.created_at.asc())
        .limit(1)
    )
    if kinds:
        q = q.where(JobRow.kind.in_(kinds))
    bind = session.get_bind()
    if bind is not None and bind.dialect.name == "postgresql":
        q = q.with_for_update(skip_locked=True)
    row = session.execute(q).scalar_one_or_none()
    if row is None:
        return None
    now = utc_now()
    row.status = "running"
    row.started_at = now
    session.flush()
    return _from_row(row)


def finish_job(
    session: Session,
    job_id: UUID,
    *,
    result: dict[str, Any] | None = None,
    error: str | None = None,
) -> None:
    row = session.get(JobRow, job_id)
    if row is None:
        return
    row.finished_at = utc_now()
    row.result = result
    row.error = error
    row.status = "failed" if error else "succeeded"


def get_job(session: Session, job_id: UUID) -> JobRecord | None:
    row = session.get(JobRow, job_id)
    return _from_row(row) if row else None


def _from_row(row: JobRow) -> JobRecord:
    return JobRecord(
        id=row.id,
        tenant_id=row.tenant_id,
        kind=row.kind,
        status=row.status,
        payload=row.payload or {},
        result=row.result,
        created_at=row.created_at,
        started_at=row.started_at,
        finished_at=row.finished_at,
        error=row.error,
    )
