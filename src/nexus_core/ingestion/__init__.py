from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from nexus_core.ingestion.connectors import fetch_raw, observations_from_raw
from nexus_core.ingestion.models import SourceConfig
from nexus_core.ingestion.store import persist_observations
from nexus_core.logging import get_logger
from nexus_core.normalization import normalize_batch

log = get_logger("nexus.ingest")


@dataclass
class IngestResult:
    source_id: str
    fetched: bool
    observation_count: int
    inserted: int
    error: str | None = None


def ingest_source(
    session: Session | None,
    source: SourceConfig,
    *,
    fixture_root: Path | None = None,
    persist: bool = True,
) -> IngestResult:
    if not source.enabled:
        return IngestResult(source.id, False, 0, 0, error="disabled")

    try:
        raw = fetch_raw(source, fixture_root=fixture_root)
        observations = observations_from_raw(source, raw)
        observations, _stats = normalize_batch(observations)
        inserted = 0
        if persist:
            if session is None:
                raise ValueError("session required when persist=True")
            inserted = persist_observations(session, observations)
        log.info(
            "ingest complete",
            extra={"source_id": source.id, "phase": "ingest"},
        )
        return IngestResult(source.id, True, len(observations), inserted)
    except Exception as exc:  # noqa: BLE001 - isolate source failures
        log.exception("ingest failed for %s", source.id)
        return IngestResult(source.id, False, 0, 0, error=str(exc))


def ingest_many(
    session: Session | None,
    sources: list[SourceConfig],
    *,
    fixture_root: Path | None = None,
    persist: bool = True,
) -> list[IngestResult]:
    results: list[IngestResult] = []
    for source in sources:
        results.append(
            ingest_source(session, source, fixture_root=fixture_root, persist=persist)
        )
    return results
