from __future__ import annotations

from pathlib import Path

from nexus_core.extraction import extract_entities, extract_events
from nexus_core.ingestion import ingest_many
from nexus_core.ingestion.registry import load_sources


def test_extract_from_fixtures() -> None:
    root = Path(__file__).resolve().parents[1]
    sources = [s for s in load_sources(root / "adapters/generic/sources.ci.yaml") if s.enabled]
    results = ingest_many(None, sources, fixture_root=root / "datasets", persist=False)
    # rebuild observations via dry path already normalized counts
    assert sum(r.observation_count for r in results) >= 3

    from nexus_core.ingestion.connectors import fetch_raw, observations_from_raw
    from nexus_core.normalization import normalize_batch

    observations = []
    for source in sources:
        raw = fetch_raw(source, fixture_root=root / "datasets")
        observations.extend(observations_from_raw(source, raw))
    observations, _ = normalize_batch(observations)
    entities = extract_entities(observations)
    events = extract_events(observations, entities)
    assert len(events) == len(observations)
    assert all(e.type for e in events)
