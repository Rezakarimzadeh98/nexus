from __future__ import annotations

import os

from api.app import app
from fastapi.testclient import TestClient

from nexus_sdk import NexusClient


def test_health_endpoint() -> None:
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert "version" in body
    assert body["status"] in {"ok", "degraded"}
    assert body["version"].startswith("1.")


def test_adapters_endpoint() -> None:
    client = TestClient(app)
    res = client.get("/v1/adapters")
    assert res.status_code == 200
    domains = {row["domain"] for row in res.json()}
    assert "generic" in domains
    assert "cyber" in domains


def test_ingest_job_dry_run_without_api_key() -> None:
    os.environ.pop("NEXUS_API_KEY", None)
    from nexus_core.config import get_settings

    get_settings.cache_clear()
    client = TestClient(app)
    res = client.post(
        "/v1/jobs/ingest",
        json={"adapter": "finance", "offline": True, "dry_run": True},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["adapter"] == "finance"
    assert body["results"]


def test_ingest_job_requires_api_key_when_set() -> None:
    os.environ["NEXUS_API_KEY"] = "test-secret-key"
    from nexus_core.config import get_settings

    get_settings.cache_clear()
    try:
        client = TestClient(app)
        denied = client.post(
            "/v1/jobs/ingest",
            json={"adapter": "generic", "offline": True, "dry_run": True},
        )
        assert denied.status_code == 401
        ok = client.post(
            "/v1/jobs/ingest",
            headers={"Authorization": "Bearer test-secret-key"},
            json={"adapter": "generic", "offline": True, "dry_run": True},
        )
        assert ok.status_code == 200
    finally:
        os.environ.pop("NEXUS_API_KEY", None)
        get_settings.cache_clear()


def test_sdk_client_constructs() -> None:
    sdk = NexusClient(base_url="http://test.example", api_key="k")
    assert sdk.base_url == "http://test.example"
    sdk.close()
