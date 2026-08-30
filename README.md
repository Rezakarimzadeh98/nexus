# NEXUS

**Universal Intelligence Engine**

Turn scattered, high-volume data into a living model of reality: what is happening now, what just changed, what it connects to, what may happen next - and whether those claims hold up against the truth.

[![License: MIT](https://img.shields.io/badge/license-MIT-0f766e.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-v0.3.0-0f766e.svg)](https://github.com/Rezakarimzadeh98/nexus/releases/tag/v0.3.0)
[![CI](https://github.com/Rezakarimzadeh98/nexus/actions/workflows/ci.yml/badge.svg)](https://github.com/Rezakarimzadeh98/nexus/actions/workflows/ci.yml)
[![Live ingest](https://github.com/Rezakarimzadeh98/nexus/actions/workflows/live-ingest.yml/badge.svg)](https://github.com/Rezakarimzadeh98/nexus/actions/workflows/live-ingest.yml)
[![Status](https://img.shields.io/badge/status-Phase_6_Show-0f766e.svg)](docs/ROADMAP.md)
[![Live demo](https://img.shields.io/badge/live-demo-3d9b7a)](https://rezakarimzadeh98.github.io/nexus/)
[![Discussions](https://img.shields.io/badge/discussions-join-1f6feb)](https://github.com/Rezakarimzadeh98/nexus/discussions)

![NEXUS social preview](docs/assets/social-preview.png)

[Product](docs/PRODUCT.md) | [Roadmap](docs/ROADMAP.md) | [Architecture](docs/ARCHITECTURE.md) | [Live snapshot](docs/live/README.md) | [Share kit](docs/SHARE.md) | [References](docs/REFERENCES.md) | [Contributing](CONTRIBUTING.md)

---

## The problem people feel

There is too much data and not enough understanding.

Sources disagree. Timelines drift. Dashboards count events but cannot say *what changed in the system*. Chat-style tools answer a prompt and forget state, provenance, and scorekeeping.

**NEXUS is built for a different job:** keep a living model, detect meaningful change, show the evidence, forecast with probability - then measure whether you were right.

---

## What NEXUS does

`	ext
10,000,000 data points
        |
   entities / events / relations
        |
     living current state
        |
   signals / patterns / forecasts
        |
   evidence / outcomes / evaluation
`

| Capability | Plain meaning |
| --- | --- |
| **Observe** | Pull heterogeneous sources continuously |
| **Understand** | Normalize time, language, duplicates |
| **Connect** | Entities, events, relationships |
| **Detect** | State shifts, signals, anomalies with explanations |
| **Discover** | Recurring patterns from history |
| **Forecast** | Probabilistic scenarios - never false certainty |
| **Verify** | Compare predictions to what actually happened |
| **Learn** | Feed errors back into thresholds and models |

![NEXUS intelligence loop](docs/assets/loop-diagram.png)

---

## Live demo (online)

Public feeds (USGS, NASA EONET, arXiv, NVD, WHO) are ingested on a schedule. The Action computes **state + signals**, then publishes a static **What Changed** page:

**https://rezakarimzadeh98.github.io/nexus/**

Snapshot JSON: [docs/live/status.json](docs/live/status.json) (refreshed on each live run / Pages deploy).

Self-host the API:

`ash
pip install -e ".[api]"
uvicorn api.app:app --reload --port 8080
# GET /health /live /signals /state/global /observations/{id}
`

---

## Not another "ask the model" stack

`	ext
Wrong shape                         NEXUS shape
-----------                         -----------
Data -> LLM -> Answer               Data -> structured intelligence
                                    -> state -> signals -> patterns
                                    -> forecast -> outcome -> evaluation
`

Large language models may help with extraction, classification, and explanation.
They are **not** the product. Forecasting and anomaly detection ship with measurable baselines first.

---

## Domain-agnostic core

The engine only knows public concepts:

Entity / Event / Observation / Relationship / State / Signal / Pattern / Forecast / Evidence / Outcome

Adapters plug domains on top - news, finance, cyber, supply chain, open analytical research - without rewriting the core.

---

## Quick start

Requirements: Python 3.11+, Docker Compose (for Postgres).

`ash
cp .env.example .env
docker compose -f infrastructure/compose.yml up -d
python -m pip install -e ".[dev,api]"
alembic upgrade head
pytest -q
python -m nexus_core.cli ingest --dry-run
python -m nexus_core.cli detect
python -m nexus_core.cli export-live
`

---

## Proof question

> Can heterogeneous public data become a living model that detects important change earlier than naive counting, explains it with source-linked evidence, and produces forecasts we can score against reality?

If benchmarks say yes, NEXUS is more than a demo - it is a platform.

---

## Roadmap at a glance

| Phase | Name | You get |
| ---: | --- | --- |
| 0 | Lock and bootstrap | Product, architecture, public repo |
| 1 | Foundation | Compose, CI, schemas, core types |
| 2-3 | Observe and understand | Ingest + normalize (official public sources) |
| 4-5 | Connect and detect | Entities/events + **state / signal / anomaly** + API |
| **6** | **Show** | Live Pages demo + richer dashboard detail |
| 7-8 | Discover and forecast | Graph, patterns, scenarios, probabilities |
| 9-10 | Verify and learn | Replay, Brier/lead-time, feedback loops |
| 11 | Platform (v1.0) | Adapters, SDK, API, web platform |
| 12 | Enterprise | Multi-tenant, SSO, SLA, scale, governance |

Every checkbox lives in [docs/ROADMAP.md](docs/ROADMAP.md).

---

## Status (honest)

**v0.3.0** - Phase 5 detect + FastAPI + public live demo. Phase 6 dashboard detail still expanding.

NEXUS is not yet a production intelligence cloud. Stars help; reproducible pipelines and public benchmarks matter more.

---

## Non-goals

- Operational military targeting or action guidance
- Treating "prompt -> answer" as the whole product
- Declaring the future as certain

---

## Get involved

- Read the [product lock](docs/PRODUCT.md) and [roadmap](docs/ROADMAP.md)
- Open a [Discussion](https://github.com/Rezakarimzadeh98/nexus/discussions) with a domain or data problem
- Take a roadmap checkbox and open a focused PR ([Contributing](CONTRIBUTING.md))

Launch copy: [docs/SHARE.md](docs/SHARE.md)

## License

MIT (c) [Reza Karimzadeh](https://github.com/Rezakarimzadeh98)
