"""Worker loop — claim queued jobs and execute pipeline kinds."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from nexus_core.config import get_settings
from nexus_core.db import make_engine, make_session_factory
from nexus_core.enterprise.jobs import claim_next_job, finish_job
from nexus_core.ingestion import ingest_many
from nexus_core.logging import configure_logging, get_logger


def process_job_payload(kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    if kind == "ingest":
        from nexus_core.adapters import get_adapter

        adapter_name = str(payload.get("adapter") or "generic")
        offline = bool(payload.get("offline", True))
        adapter = get_adapter(adapter_name)
        sources = adapter.load_source_configs(offline=offline)
        fixture_root = Path(str(payload.get("fixture_root") or "datasets"))
        settings = get_settings()
        engine = make_engine(settings)
        factory = make_session_factory(engine)
        with factory() as session:
            results = ingest_many(session, sources, fixture_root=fixture_root, persist=True)
            session.commit()
        return {
            "results": [
                {
                    "source_id": r.source_id,
                    "inserted": r.inserted,
                    "error": r.error,
                }
                for r in results
            ]
        }
    if kind == "retention":
        from uuid import UUID

        from nexus_core.enterprise.retention import apply_retention

        settings = get_settings()
        engine = make_engine(settings)
        factory = make_session_factory(engine)
        tenant_raw = payload.get("tenant_id")
        tenant_id = UUID(str(tenant_raw)) if tenant_raw else None
        with factory() as session:
            out = apply_retention(session, tenant_id=tenant_id)
            session.commit()
        return out
    raise ValueError(f"unsupported job kind: {kind}")


def run_worker_once() -> bool:
    settings = get_settings()
    engine = make_engine(settings)
    factory = make_session_factory(engine)
    with factory() as session:
        job = claim_next_job(session)
        if job is None:
            session.commit()
            return False
        session.commit()
        try:
            result = process_job_payload(job.kind, job.payload)
            with factory() as s2:
                finish_job(s2, job.id, result=result)
                s2.commit()
        except Exception as exc:  # noqa: BLE001 — worker must mark failure
            with factory() as s2:
                finish_job(s2, job.id, error=str(exc))
                s2.commit()
        return True


def run_worker_loop(*, idle_sleep: float = 2.0, max_iterations: int | None = None) -> None:
    configure_logging(get_settings().log_level)
    log = get_logger("nexus.worker")
    n = 0
    while max_iterations is None or n < max_iterations:
        did = run_worker_once()
        n += 1
        if not did:
            time.sleep(idle_sleep)
        else:
            log.info("job_processed iteration=%s", n)
