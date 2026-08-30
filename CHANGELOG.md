# Changelog

All notable changes to NEXUS are documented here.

## [Unreleased]

### Added

- Phase 1 foundation: `nexus_core` package, settings, structured logging, UTC/id helpers
- PostgreSQL schema v1 + Alembic migration `0001_initial`
- Docker Compose for Postgres (optional Redis profile)
- Core Pydantic contracts + JSON Schema export under `docs/schemas/v1`
- CI: ruff, mypy, pytest, schema export, alembic upgrade, DB ping
