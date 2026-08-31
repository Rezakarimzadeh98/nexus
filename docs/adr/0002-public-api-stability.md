# ADR-0002 — Public API stability (v1.0)

## Status

Accepted (Phase 11)

## Context

NEXUS needs a honest claim that it is an OSS **platform**: frozen interchange types,
documented adapters, SDK, and authenticated write paths — without freezing every
internal engine heuristic.

## Decision

### Semver (package `nexus-core` / API `version`)

| Surface | Stability |
| --- | --- |
| `docs/schemas/v1/*.schema.json` | **Public** — additive changes OK; breaking changes require `v2` |
| Pydantic models in `nexus_core.types` (+ Forecast / Outcome / Pattern exports) | **Public** |
| `DomainAdapter` / `FileDomainAdapter` / `get_adapter` | **Public** |
| HTTP GET routes under `/`, `/health`, `/live`, `/signals`, … | **Public** |
| HTTP write routes under `/v1/jobs/*` | **Public** (require API key) |
| Python SDK `nexus_sdk` | **Public** |
| Engine heuristics (thresholds, hazard rate constants) | **Internal** — may change in patch/minor |

### Auth

- Read paths remain open for the public demo.
- Write paths require `Authorization: Bearer <NEXUS_API_KEY>` when `NEXUS_API_KEY` is set.
- If `NEXUS_API_KEY` is empty (local/dev), write paths are allowed with a warning header.

## Consequences

- Schema export CI must cover Forecast / Outcome / Pattern families.
- OpenAPI artifact published at `docs/openapi/v1.json`.
- Breaking core field renames wait for a major version.
