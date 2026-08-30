from __future__ import annotations

from pathlib import Path

from nexus_core.ingestion import ingest_many
from nexus_core.ingestion.registry import load_sources


def test_load_and_dry_run_fixtures() -> None:
    root = Path(__file__).resolve().parents[1]
    sources = load_sources(root / "adapters/generic/sources.yaml")
    enabled = [s for s in sources if s.enabled]
    assert len(enabled) >= 2
    results = ingest_many(
        None,
        enabled,
        fixture_root=root / "datasets",
        persist=False,
    )
    assert all(r.error is None for r in results)
    assert sum(r.observation_count for r in results) >= 3


def test_item_fingerprint_stable() -> None:
    from nexus_core.ingestion.connectors import item_fingerprint

    a = item_fingerprint("s", "t", "https://example.com/a", "b")
    b = item_fingerprint("s", "t", "https://example.com/a", "b")
    c = item_fingerprint("s", "t", "https://example.com/a", "other")
    assert a == b
    assert a != c
