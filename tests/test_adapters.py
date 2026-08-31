from __future__ import annotations

from pathlib import Path

from nexus_core.adapters import get_adapter, list_adapters
from nexus_core.ingestion import ingest_many


def test_list_adapters_covers_v1_domains() -> None:
    domains = {a.domain for a in list_adapters()}
    assert domains == {"generic", "finance", "cyber", "supply_chain", "defense"}


def test_generic_adapter_loads_ci_sources() -> None:
    adapter = get_adapter("generic")
    sources = adapter.load_source_configs(offline=True)
    assert len(sources) >= 1
    assert adapter.sources_path(offline=True).name == "sources.ci.yaml"


def test_all_adapters_dry_run_ci_fixtures() -> None:
    root = Path("datasets")
    for adapter in list_adapters():
        sources = adapter.load_source_configs(offline=True)
        results = ingest_many(None, sources, fixture_root=root, persist=False)
        assert results
        assert all(r.error is None for r in results), [(r.source_id, r.error) for r in results]
        assert sum(r.observation_count for r in results) >= 1
