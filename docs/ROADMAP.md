# NEXUS — Master roadmap (to enterprise)

This is the **single source of truth** for phasing.  
Maintainers track the *current* phase in issues/PRs; this file tracks the whole program.

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
**Status: DONE** · Goal: runnable empty platform

### 1.1 Monorepo / package layout
- [x] Python package `nexus_core`
- [x] Shared config (env, settings)
- [x] Logging + structured logs
- [x] ID / time utilities (UTC everywhere)

### 1.2 Persistence
- [x] PostgreSQL schema v1 (observations, entities, events, states, signals)
- [x] Migrations (Alembic or equivalent)
- [x] Docker Compose: Postgres (+ Redis optional)

### 1.3 Quality gates
- [x] pytest + ruff/mypy baseline
- [x] GitHub Actions CI (lint, test, migrate smoke)
- [x] Pre-commit optional

### 1.4 Core types (contracts only)
- [x] Typed models: Observation, Entity, Event, Relation, StateSnapshot, Signal, EvidenceRef
- [x] Versioned JSON schemas for interchange

**Exit:** `docker compose up` + empty migrate + CI green on Hello World. ✅ (Compose + Alembic in repo; CI runs migrate + DB ping)

---

## Phase 2 — Observe (Ingestion)
**Status: DONE**

### 2.1 Ingestion engine
- [x] Source registry (id, type, schedule, credentials ref)
- [x] Connectors: RSS, HTTP JSON, CSV file, static fixture
- [x] Job runner (cron / CLI `nexus ingest`)
- [x] Raw blob store + content hash (dedupe at raw layer)

### 2.2 First sources (5–10 public)
- [x] Curate list in `adapters/generic/sources.yaml`
- [x] Rate limits + robots/ToS respect
- [x] Failure isolation per source

### 2.3 Provenance
- [x] Every observation links to `source_id`, `fetched_at`, `raw_uri` / hash

**Exit:** Continuous or on-demand ingest writes observations with provenance. ✅

---

## Phase 3 — Understand + Normalize
**Status: DONE**

### 3.1 Normalization engine
- [x] Canonical time (UTC)
- [x] Language detect (optional)
- [x] Text cleanup / empty drop
- [x] Near-duplicate detection (title+time+source)

### 3.2 Canonical observation schema
- [x] `title`, `body`, `published_at`, `url`, `source_id`, `lang`, `raw_ref`

### 3.3 Quality metrics
- [x] % failed parses, dup rate, lag histogram

**Exit:** Normalized observations queryable; dup rate measured. ✅ (batch stats + ingest path)

---

## Phase 4 — Connect (Entity + Event + optional LLM assist)
**Status: DONE** (v0.2 core; LLM assist + full resolution deferred)

### 4.1 Entity engine
- [x] Rule/heuristic extractors (ORG, PERSON, GPE, PRODUCT…) — initial ORG heuristics
- [ ] Optional LLM extract path behind interface (deferred)
- [ ] Entity resolution (same real-world thing → one id) (deferred)
- [x] Entity store + aliases (store + aliases field)

### 4.2 Event engine
- [x] Event types for generic domain (Announcement, Agreement, Conflict, MarketMove, …) — starter set
- [x] Link events ↔ entities ↔ observations — observation + entity id lists
- [x] Confidence on extractions

### 4.3 Relationship engine (minimal)
- [x] Edges: `reports_on` (org↔location) + persist
- [x] Persist for graph phase

**Exit:** Pipeline observation → entities/events with links back to sources. ✅

---

## Phase 5 — Detect (State + Signal + Anomaly) = **v0.1 core**
**Status: DONE** · shipped in **v0.3.0**

### 5.1 State engine
- [x] Scope keys (global + `source:{id}`; entity/region/topic later)
- [x] Rolling metrics: volume, velocity, recency
- [x] State snapshots over time (persisted)

### 5.2 Signal engine
- [x] Baselines (7d window vs 24h short)
- [x] Deviation scores (volume, velocity, source diversity)
- [x] Signal object: magnitude, confidence, window, scope

### 5.3 Anomaly engine
- [x] Statistical anomaly flags
- [x] Human-readable “why” template (features that fired)
- [x] Severity levels

### 5.4 Evidence engine (v0.1)
- [x] Attach supporting observation ids / titles
- [x] Contradictions placeholder list

### 5.5 API
- [x] FastAPI: `/health`, `/live`, `/signals`, `/signals/{id}`, `/state/{scope}`, `/observations/{id}`
- [x] Public live snapshot + GitHub Pages demo

**Exit criterion (v0.1 product):**  
Dashboard or API can show **What Changed** with **confidence + evidence links**. ✅

---

## Phase 6 — Show (Dashboard v0.1 + site shell)
**Status: DONE** · shipped in **v0.3.1**

### 6.1 Dashboard
- [x] Live counters (data, entities, events, signals) — Pages demo
- [x] Signal feed (“What Changed?”) — Pages demo
- [x] Signal detail: metrics, evidence links, related observations
- [x] Dark-neutral readable UI (not generic purple SaaS)

### 6.2 Deploy
- [x] Compose includes API + web
- [x] GitHub Pages live demo from scheduled ingest
- [ ] Optional Vercel/static for marketing shell later

**Exit:** Visitor understands NEXUS in 60 seconds from UI. ✅

---

## Phase 7 — Discover (Graph + Patterns) = **v0.2 product slice**
**Status: DONE** · shipped in **v0.4.0**

### 7.1 Knowledge graph
- [x] Query API for neighborhood (`/graph/neighborhood`)
- [x] Dashboard graph view (scoped hub neighborhood)

### 7.2 Pattern engine
- [x] Mine frequent sequences A→B→C (support/confidence)
- [x] Pattern match alerts when prefix repeats
- [x] Link patterns to historical examples (example event ids)

**Exit:** “We’ve seen this shape before” with examples. ✅

---

## Phase 8 — Forecast + Scenarios = **v0.3 product slice**
**Status: DONE** · shipped in **v0.5.0**

### 8.1 Forecast engine
- [x] Explicit question schema (event-in-horizon, risk trajectory)
- [x] Outputs: probability, confidence, horizon, evidence ids
- [x] Non-LLM baselines first (hazard rates, simple models)
- [x] Optional model registry in `models/` (`registry.yaml`)

### 8.2 Scenario engine
- [x] 2–N scenarios with probabilities summing ~1
- [x] Drivers listed per scenario

### 8.3 UI
- [x] Forecast cards + scenario split view

**Exit:** Forecasts always carry probability + evidence; never certainty claims. ✅

---

## Phase 9 — Verify + Evaluate = **v0.4 product slice**
**Status: DONE** · shipped in **v0.6.0**

### 9.1 Historical replay
- [x] Time-travel ingest cutoff
- [x] Blind forecast protocol

### 9.2 Evaluation engine
- [x] Precision/Recall/F1 for signals vs labeled changes (velocity-proxy labels)
- [x] Brier score + calibration for forecasts
- [x] Detection lead time vs naive baseline
- [x] False positive rate dashboards

### 9.3 Benchmarks package
- [x] Public benchmark definition + scripts in `benchmarks/`
- [x] Published baseline numbers in docs (`docs/BENCHMARKS.md` + live scorecard)

**Exit:** Proof question answerable with numbers, not vibes. ✅

---

## Phase 10 — Learn (Feedback) = **v0.5**
**Status: ACTIVE**

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
5. Day-to-day work should mirror the Active phase sub-tasks only.  
6. Public copy stays under the maintainer’s name and profile only — no internal tooling, assistant, or vendor branding in README, UI, docs, or release notes.
