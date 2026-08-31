from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from nexus_core.db.models import Base
from nexus_core.enterprise.audit import AuditEvent, record_audit
from nexus_core.enterprise.jobs import JobRecord, claim_next_job, enqueue_job, finish_job
from nexus_core.enterprise.oidc import validate_oidc_bearer
from nexus_core.enterprise.pii import redact_mapping, redact_text
from nexus_core.enterprise.rbac import role_allows
from nexus_core.enterprise.tenancy import Tenant, create_tenant, get_tenant_by_slug, list_tenants

_HAS_PG = "postgresql" in os.environ.get("NEXUS_DATABASE_URL", "")


def test_rbac_ranks() -> None:
    assert role_allows("viewer", "read")
    assert not role_allows("viewer", "ingest")
    assert role_allows("operator", "ingest")
    assert role_allows("admin", "tenant.write")


def test_pii_redaction() -> None:
    assert "[REDACTED_EMAIL]" in redact_text("mail me at a@b.co please")
    out = redact_mapping({"email": "a@b.co", "title": "ok"})
    assert out["email"] == "[REDACTED]"
    assert out["title"] == "ok"


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def test_oidc_hs256_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    secret = "test-oidc-secret"
    monkeypatch.setenv("NEXUS_OIDC_CLIENT_SECRET", secret)
    monkeypatch.setenv("NEXUS_OIDC_AUDIENCE", "nexus")
    from nexus_core.config import get_settings

    get_settings.cache_clear()

    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64url(
        json.dumps({"sub": "user-1", "aud": "nexus", "exp": int(time.time()) + 3600}).encode()
    )
    sig = hmac.new(secret.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
    token = f"{header}.{payload}.{_b64url(sig)}"
    claims = validate_oidc_bearer(token)
    assert claims is not None
    assert claims["sub"] == "user-1"
    get_settings.cache_clear()


@pytest.mark.skipif(not _HAS_PG, reason="Postgres required for enterprise table integration")
def test_tenant_and_audit_roundtrip() -> None:
    url = os.environ["NEXUS_DATABASE_URL"]
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    session: Session = factory()
    try:
        slug = f"acme-{int(time.time())}"
        tenant = Tenant(slug=slug, name="Acme", region="eu-west")
        create_tenant(session, tenant)
        session.commit()
        got = get_tenant_by_slug(session, slug)
        assert got is not None
        assert got.region == "eu-west"
        record_audit(
            session,
            AuditEvent(
                tenant_id=tenant.id,
                actor="tester",
                action="tenant.create",
                resource=slug,
            ),
        )
        session.commit()
        assert any(t.slug == slug for t in list_tenants(session))
    finally:
        session.close()


@pytest.mark.skipif(not _HAS_PG, reason="Postgres required for enterprise table integration")
def test_job_queue_claim_finish() -> None:
    url = os.environ["NEXUS_DATABASE_URL"]
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    session: Session = factory()
    try:
        job = JobRecord(kind="retention", payload={})
        enqueue_job(session, job)
        session.commit()
        claimed = claim_next_job(session)
        assert claimed is not None
        assert claimed.status == "running"
        session.commit()
        finish_job(session, claimed.id, result={"deleted_observations": 0})
        session.commit()
    finally:
        session.close()
