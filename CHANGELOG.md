# Changelog

All notable changes to NEXUS are documented here.

## [0.6.0] - 2026-08-30

### Added

- Phase 9 evaluation: blind forecast protocol, Brier score, precision/recall/F1, FPR, lead time
- CLI `nexus evaluate`; API `/evaluation`; live Scorecard panel
- `benchmarks/definitions/v1.yaml`, `benchmarks/run_baseline.py`, `docs/BENCHMARKS.md`

### Changed

- Package version **0.6.0**

## [0.5.0] - 2026-08-30

### Added

- Phase 8 forecasts: explicit questions, hazard-rate baseline (`hazard_rate_v1`), evidence ids
- Scenario engine (elevated / status_quo / cooling) with probabilities summing ~1
- CLI `nexus forecast`; API `/forecasts`, `/forecasts/{id}`
- `models/registry.yaml`; Alembic `0003_forecasts`; dashboard forecast cards + scenario split

### Changed

- Package version **0.5.0**

## [0.4.0] - 2026-08-30

### Added

- Phase 7 discovery: scoped entity neighborhood graph + sequence pattern mining (A->B->C)
- Pattern match alerts when a recent prefix historically continues
- CLI `nexus discover`; API `/graph/neighborhood`, `/patterns`
- Alembic `0002_patterns`; dashboard Seen before + Neighborhood views

### Changed

- Package version **0.4.0**

## [0.3.1] - 2026-08-30

### Added

- Phase 6 dashboard signal detail (metrics + evidence links)
- Compose stack: Postgres + API + nginx web UI
- `AUTHORS.md` — maintainer Reza Karimzadeh
- Snapshot fields: `maintainer`, `observations_by_id`

### Changed

- Public copy attributes the project to Reza Karimzadeh / profile only
- Package version **0.3.1**

## [0.3.0] - 2026-08-30

### Added

- Phase 5 detection: state snapshots, velocity signals, anomaly severity + why text, evidence refs
- CLI: `nexus detect`, `nexus export-live`
- FastAPI app (`api.app`): `/health`, `/live`, `/signals`, `/state/{scope}`, `/observations/{id}`
- Public dashboard (`dashboard/index.html`) deployed to GitHub Pages from live ingest
- Live ingest Action now detects, exports snapshot, and publishes Pages

### Changed

- Package version **0.3.0**; Phase 4 marked done (optional extract assist + resolution deferred)

## [0.2.0] - 2026-08-30

### Added

- Official live sources with citations: USGS GeoJSON, NASA EONET, arXiv Atom, NIST NVD CVE API, WHO news RSS
- `docs/REFERENCES.md` and `adapters/generic/sources.ci.yaml` for offline CI
- `nexus extract` / `nexus status` CLI; entity/event/relation persistence helpers
- Scheduled GitHub Action `live-ingest.yml` for dynamic official ingest

### Changed

- Default `sources.yaml` is live official feeds (fixtures only in CI file)
- Package version **0.2.0**
