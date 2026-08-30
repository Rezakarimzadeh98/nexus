# NEXUS — Architecture (v0 outline)

## Loop

```text
OBSERVE → UNDERSTAND → CONNECT → DETECT → DISCOVER → FORECAST → VERIFY → LEARN
```

Engines map 1:1 onto folders under `core/`. Adapters only translate domain vocabulary into core types.

## Core concepts

| Concept | Meaning |
| --- | --- |
| Observation | Normalized fact from a source at a time |
| Entity | Thing in the world (org, person, place, …) |
| Event | Something that happened involving entities |
| Relationship | Edge between entities/events |
| State | Living metrics for a scope at time T |
| Signal | Attention-worthy change vs baseline |
| Pattern | Recurring structure in history |
| Forecast | Probabilistic claim + horizon + evidence |
| Evidence | Links back to observations/sources |
| Outcome | Ground truth used for evaluation |

## LLM boundary

LLM **may** implement extractors behind interfaces (`EntityExtractor`, `EventExtractor`, `Explainer`).  
LLM **must not** be the sole forecast or anomaly authority in v0.x.

## Data flow (v0.1)

```text
Sources → Ingestion → Raw store
              ↓
         Normalization → Observations (Postgres)
              ↓
         Entity/Event extract → Entities / Events
              ↓
         State updater → State snapshots
              ↓
         Signal/Anomaly → Signals + Evidence
              ↓
         API → Dashboard
```

## Persistence

PostgreSQL is system of record for v0–v1.  
Graph query can start as relational + materialized paths; dedicated graph DB is a later option (ADR required).

## Deployment

- Dev: Docker Compose (Postgres, API, worker, dashboard)
- Prod path (enterprise): Kubernetes + object storage for raw blobs + managed Postgres

## ADRs

See `docs/adr/`. New engine boundary or storage choice = new ADR.
