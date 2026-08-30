from __future__ import annotations

from api.app import app
from fastapi.testclient import TestClient


def test_health_endpoint() -> None:
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert "version" in body
    assert body["status"] in {"ok", "degraded"}
