# Changelog

All notable changes to NEXUS are documented here.

## [0.3.0] - 2026-08-30

### Added

- Phase 5 detection: state snapshots, velocity signals, anomaly severity + why text, evidence refs
- CLI: `nexus detect`, `nexus export-live`
- FastAPI app (`api.app`): `/health`, `/live`, `/signals`, `/state/{scope}`, `/observations/{id}`
- Public dashboard (`dashboard/index.html`) deployed to GitHub Pages from live ingest
- Live ingest Action now detects, exports snapshot, and publishes Pages

### Changed

- Package version **0.3.0**; Phase 4 marked done (LLM/resolution deferred)

## [0.2.0] - 2026-08-30

### Added

- Official live sources with citations: USGS GeoJSON, NASA EONET, arXiv Atom, NIST NVD CVE API, WHO news RSS
- `docs/REFERENCES.md` and `adapters/generic/sources.ci.yaml` for offline CI
- `nexus extract` / `nexus status` CLI; entity/event/relation persistence helpers
- Scheduled GitHub Action `live-ingest.yml` for dynamic official ingest

### Changed

- Default `sources.yaml` is live official feeds (fixtures only in CI file)
- Package version **0.2.0**
