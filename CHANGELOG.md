# Changelog

All notable changes to NEXUS are documented here.

## [0.2.0] - 2026-08-30

### Added

- Official live sources with citations: USGS GeoJSON, NASA EONET, arXiv Atom, NIST NVD CVE API, WHO news RSS
- `docs/REFERENCES.md` and `adapters/generic/sources.ci.yaml` for offline CI
- `nexus extract` / `nexus status` CLI; entity/event/relation persistence helpers
- Scheduled GitHub Action `live-ingest.yml` for dynamic official ingest

### Changed

- Default `sources.yaml` is live official feeds (fixtures only in CI file)
- Package version **0.2.0**
