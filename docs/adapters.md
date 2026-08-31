# Domain adapters

NEXUS keeps a **domain-agnostic core**. Adapters only:

1. Declare domain metadata (`domain`, display name, non-goals).
2. Point at `sources.yaml` / `sources.ci.yaml` the ingestion engine already understands.
3. Optionally annotate observations with `metadata.domain`.

They do **not** invent new core types or bypass provenance.

## Stable interface (1.x)

```python
from nexus_core.adapters import get_adapter, list_adapters

for adapter in list_adapters():
    print(adapter.domain, adapter.display_name)

finance = get_adapter("finance")
sources = finance.load_source_configs(offline=True)  # CI fixtures
live_path = finance.sources_path(offline=False)
```

Protocol: `nexus_core.adapters.DomainAdapter`  
Default implementation: `FileDomainAdapter` under `adapters/<domain>/`.

## Packs shipped in v1.0

| Domain | Path | Notes |
| --- | --- | --- |
| `generic` | `adapters/generic/` | Hazards, science, health (default demo) |
| `finance` | `adapters/finance/` | Public SEC EDGAR Atom |
| `cyber` | `adapters/cyber/` | NVD + CISA KEV |
| `supply_chain` | `adapters/supply_chain/` | Public logistics RSS + fixtures |
| `defense` | `adapters/defense/` | **Open analytical only** (ReliefWeb); non-operational |

## CLI

```bash
nexus ingest --adapter cyber --dry-run
nexus ingest --adapter finance --sources adapters/finance/sources.ci.yaml --fixture-root datasets
nexus sources --adapter generic
```

`--adapter` resolves to `adapters/<name>/sources.yaml` unless `--sources` is set.

## Example: add a new adapter

1. Create `adapters/my_domain/sources.yaml` and `sources.ci.yaml`.
2. Register a `FileDomainAdapter` in `src/nexus_core/adapters/base.py`.
3. Add fixtures under `datasets/fixtures/` and a short README.
4. Extend CI to dry-run the new pack.

See [ADR-0001](adr/0001-domain-agnostic-core.md) and [ADR-0002](adr/0002-public-api-stability.md).
