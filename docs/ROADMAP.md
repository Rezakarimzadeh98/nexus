# NEXUS — Master roadmap (to enterprise)

This is the **single source of truth** for phasing.  
Session todos track the *current* phase; this file tracks the whole program.

Status legend: `PLANNED` · `ACTIVE` · `DONE` · `BLOCKED`

---

## Phase 0 — Lock & bootstrap
**Status: DONE** · Goal: identity, repo, docs, empty skeleton

### 0.1 Product lock
- [x] One-line definition
- [x] Non-goals + first wedge
- [x] Proof question
- [x] CONTRIBUTING / SECURITY / CODE_OF_CONDUCT
- [x] Public GitHub repo + topics + description

### 0.2 Documentation spine
- [x] PRODUCT.md
- [x] ROADMAP.md (this file)
- [x] ARCHITECTURE.md
- [x] ADRs folder + ADR-0001 core concepts
- [x] SHARE.md (launch / viral copy kit)
- [x] Public visuals (social preview, loop diagram, dashboard north star)

### 0.3 Repo skeleton
- [x] Directory tree (`core/`, `adapters/`, `api/`, `dashboard/`, …)
- [x] Root README with links to product + roadmap
- [x] `.gitignore`, license MIT (`pyproject.toml` in Phase 1)

**Exit:** Public repo exists; anyone reading README understands v0.1 vs enterprise. ✅

---

## Phase 1 — Foundation
**Status: ACTIVE** · Goal: runnable empty platform

### 1.1 Monorepo / package layout
- [ ] Python package `nexus_core`
- [ ] Shared config (env, settings)
- [ ] Logging + structured logs
- [ ] ID / time utilities (UTC everywhere)

### 1.2 Persistence
- [ ] PostgreSQL schema v1 (observations, entities, events, states, signals)
- [ ] Migrations (Alembic or equivalent)
- [ ] Docker Compose: Postgres (+ Redis optional)

### 1.3 Quality gates
- [ ] pytest + ruff/mypy baseline
- [ ] GitHub Actions CI (lint, test, migrate smoke)
- [ ] Pre-commit optional

### 1.4 Core types (contracts only)
- [ ] Typed models: Observation, Entity, Event, Relation, StateSnapshot, Signal, EvidenceRef
- [ ] Versioned JSON schemas for interchange

**Exit:** `docker compose up` + empty migrate + CI green on Hello World.

---

## Phase 2 — Observe (Ingestion)
**Status: PLANNED**

### 2.1 Ingestion engine
- [ ] Source registry (id, type, schedule, credentials ref)
- [ ] Connectors: RSS, HTTP JSON, CSV file, static fixture
- [ ] Job runner (cron / CLI `nexus ingest`)
- [ ] Raw blob store + content hash (dedupe at raw layer)

### 2.2 First sources (5–10 public)
- [ ] Curate list in `adapters/generic/sources.yaml`
- [ ] Rate limits + robots/ToS respect
- [ ] Failure isolation per source

### 2.3 Provenance
- [ ] Every observation links to `source_id`, `fetched_at`, `raw_uri` / hash

**Exit:** Continuous or on-demand ingest writes observations with provenance.

---

## Phase 3 — Understand + Normalize
**Status: PLANNED**

### 3.1 Normalization engine
- [ ] Canonical time (UTC)
- [ ] Language detect (optional)
- [ ] Text cleanup / empty drop
- [ ] Near-duplicate detection (title+time+source)

### 3.2 Canonical observation schema
- [ ] `title`, `body`, `published_at`, `url`, `source_id`, `lang`, `raw_ref`

### 3.3 Quality metrics
- [ ] % failed parses, dup rate, lag histogram

**Exit:** Normalized observations queryable; dup rate measured.

---

## Phase 4 — Connect (Entity + Event + optional LLM assist)
**Status: PLANNED**

### 4.1 Entity engine
- [ ] Rule/heuristic extractors (ORG, PERSON, GPE, PRODUCT…)
- [ ] Optional LLM extract path behind interface
- [ ] Entity resolution (same real-world thing → one id)
- [ ] Entity store + aliases

### 4.2 Event engine
- [ ] Event types for generic domain (Announcement, Agreement, Conflict, MarketMove, …)
- [ ] Link events ↔ entities ↔ observations
- [ ] Confidence on extractions

### 4.3 Relationship engine (minimal)
- [ ] Edges: `mentioned_with`, `located_in`, `org_of` (expand later)
- [ ] Persist for graph phase

**Exit:** Pipeline observation → entities/events with links back to sources.

---

## Phase 5 — Detect (State + Signal + Anomaly) = **v0.1 core**
**Status: PLANNED**

### 5.1 State engine
- [ ] Scope keys (entity, region, topic, global)
- [ ] Rolling metrics: volume, velocity, recency
- [ ] State snapshots over time

### 5.2 Signal engine
- [ ] Baselines (e.g. 7d/30d)
- [ ] Deviation scores (volume, velocity, source diversity)
- [ ] Signal object: magnitude, confidence, window, scope

### 5.3 Anomaly engine
- [ ] Statistical anomaly flags
- [ ] Human-readable “why” template (features that fired)
- [ ] Severity levels

### 5.4 Evidence engine (v0.1)
- [ ] Attach supporting observation ids / urls
- [ ] Contradictions placeholder list

### 5.5 API
- [ ] FastAPI: `/health`, `/signals`, `/signals/{id}`, `/state/{scope}`, `/observations/{id}`

**Exit criterion (v0.1 product):**  
Dashboard or API can show **What Changed** with **confidence + evidence links**. Proof question partially answered for detection.

---

## Phase 6 — Show (Dashboard v0.1 + site shell)
**Status: PLANNED**

### 6.1 Dashboard
- [ ] Live counters (data, entities, events, signals)
- [ ] Signal feed (“What Changed?”)
- [ ] Signal detail: timeline snippet, evidence, related entities
- [ ] Dark-neutral readable UI (not generic purple SaaS)

### 6.2 Deploy
- [ ] Compose includes API + web
- [ ] Optional Vercel/static for marketing shell later

**Exit:** Visitor understands NEXUS in 60 seconds from UI.

---

## Phase 7 — Discover (Graph + Patterns) = **v0.2**
**Status: PLANNED**

### 7.1 Knowledge graph
- [ ] Query API for neighborhood
- [ ] Dashboard graph view (scoped, not whole-world dump)

### 7.2 Pattern engine
- [ ] Mine frequent sequences A→B→C (support/confidence)
- [ ] Pattern match alerts when prefix repeats
- [ ] Link patterns to historical examples

**Exit:** “We’ve seen this shape before” with examples.

---

## Phase 8 — Forecast + Scenarios = **v0.3**
**Status: PLANNED**

### 8.1 Forecast engine
- [ ] Explicit question schema (event-in-horizon, risk trajectory)
- [ ] Outputs: probability, confidence, horizon, evidence ids
- [ ] Non-LLM baselines first (hazard rates, simple models)
- [ ] Optional model registry in `models/`

### 8.2 Scenario engine
- [ ] 2–N scenarios with probabilities summing ~1
- [ ] Drivers listed per scenario

### 8.3 UI
- [ ] Forecast cards + scenario split view

**Exit:** Forecasts always carry probability + evidence; never certainty claims.

---

## Phase 9 — Verify + Evaluate = **v0.4**
**Status: PLANNED**

### 9.1 Historical replay
- [ ] Time-travel ingest cutoff
- [ ] Blind forecast protocol

### 9.2 Evaluation engine
- [ ] Precision/Recall/F1 for signals vs labeled changes
- [ ] Brier score + calibration for forecasts
- [ ] Detection lead time vs naive baseline
- [ ] False positive rate dashboards

### 9.3 Benchmarks package
- [ ] Public benchmark definition + scripts in `benchmarks/`
- [ ] Published baseline numbers in docs

**Exit:** Proof question answerable with numbers, not vibes.

---

## Phase 10 — Learn (Feedback) = **v0.5**
**Status: PLANNED**

### 10.1 Feedback engine
- [ ] Store prediction vs actual outcome
- [ ] Error analysis reports
- [ ] Retrain / recalibrate hooks

### 10.2 Self-evaluation loops
- [ ] Scheduled scorecards
- [ ] Regression gates in CI on benchmark subset

**Exit:** Models/thresholds improve from recorded outcomes.

---

## Phase 11 — Platformize = **v1.0**
**Status: PLANNED**

### 11.1 Generic core freeze
- [ ] Stable public APIs / schemas (semver)
- [ ] Adapter interface documented + example

### 11.2 Domain adapters
- [ ] `generic` (default)
- [ ] `finance` (public market data)
- [ ] `cyber` (public vuln/incident feeds)
- [ ] `supply_chain` (public trade/shipping if available)
- [ ] `defense` (**open-source analytical only**, non-operational)

### 11.3 SDK + API
- [ ] Python SDK
- [ ] OpenAPI complete
- [ ] Auth for write paths

### 11.4 Web platform
- [ ] Marketing site + live demo environment
- [ ] Docs portal

**Exit:** “Framework + Engine + Research + OSS platform” claim is honest.

---

## Phase 12 — Enterprise
**Status: PLANNED**

### 12.1 Tenancy & identity
- [ ] Multi-tenant isolation
- [ ] SSO (OIDC/SAML)
- [ ] RBAC / audit logs

### 12.2 Reliability & scale
- [ ] Horizontal workers / queues
- [ ] SLOs, alerting, on-call runbooks
- [ ] Backup/DR, retention policies
- [ ] Cost controls per tenant

### 12.3 Governance & compliance
- [ ] Data residency options
- [ ] PII handling policies
- [ ] Model/card docs + risk register
- [ ] Customer admin console

### 12.4 Commercial packaging
- [ ] Helm/K8s production chart
- [ ] Enterprise license tier (if dual-license later) or support contracts
- [ ] SLA definitions
- [ ] Migration/import tools

### 12.5 Security hardening
- [ ] Pen-test readiness
- [ ] Secrets management
- [ ] Supply-chain provenance (SBOMs, signed releases)

**Exit:** Sellable enterprise deployment of the same core.

---

## Cross-cutting (all phases)

| Track | Always on |
| --- | --- |
| Docs | ADRs for engine boundaries |
| Ethics | No operational harm tooling; public data ToS |
| Observability | Metrics on every pipeline stage |
| Testing | Unit + contract + golden pipeline fixtures |
| Release | Changelog + semver tags |

---

## Execution rules (maintainers)

1. Only one **ACTIVE** major phase at a time (plus small docs/visual fixes).  
2. Do not start Phase N+1 until Phase N **Exit** is checked.  
3. Prefer a vertical slice (one path works end-to-end) over empty engine stubs.  
4. Update this file’s checkboxes when work lands; refresh README status and public visuals.  
5. Session work should mirror the Active phase sub-tasks only.  
6. Public copy stays free of internal tooling names; the project speaks for itself.
