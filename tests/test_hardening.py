from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import Column, MetaData, String, Table, select

from nexus_core.enterprise.quota import QuotaExceeded, assert_ingest_quota
from nexus_core.enterprise.scoping import apply_tenant_filter


def test_apply_tenant_filter() -> None:
    meta = MetaData()
    t = Table("demo", meta, Column("id", String), Column("tenant_id", String))
    stmt = select(t.c.id)
    filtered = apply_tenant_filter(stmt, column=t.c.tenant_id, tenant_id=uuid4())
    assert "tenant_id" in str(filtered)


def test_quota_exceeded_message() -> None:
    err = QuotaExceeded("acme", 100, 100)
    assert "acme" in str(err)
    assert err.used == 100
    assert err.limit == 100


def test_assert_ingest_quota_noop_without_tenant(monkeypatch: pytest.MonkeyPatch) -> None:
    class _S:
        def get(self, *_a, **_k):  # noqa: ANN001
            return None

    assert_ingest_quota(_S(), uuid4(), incoming=10)  # type: ignore[arg-type]
