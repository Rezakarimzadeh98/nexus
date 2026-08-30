# NEXUS — Product lock

**One-line definition**

> NEXUS is a self-improving intelligence engine that turns large, heterogeneous data into a living model of reality: it detects meaningful change, explains it with evidence, forecasts probable paths, and improves by comparing predictions to outcomes.

## What it is

- Domain-agnostic **core** (Entity, Event, Observation, Relationship, State, Signal, Pattern, Forecast, Evidence, Outcome)
- **Adapters** that map domains (generic news, finance, cyber, supply chain, defense *analysis*) onto that core
- Pipelines + API + dashboard + benchmarks — not “LLM answers a question”

## What it is not

- A chat wrapper over documents
- An operational military targeting / action system
- A promise of certainty about the future
- All engines shipped on day one

## Proof question (must stay true through v1.0)

> Can we build a living model from heterogeneous public data that detects important changes earlier than naive counting, explains them with source-linked evidence, and produces forecasts that can be scored against reality?

## Default first wedge (locked)

| Decision | Choice |
| --- | --- |
| First domain | **Generic public news/events** (5–10 sources) |
| First user surface | **What Changed / Signals + Evidence** |
| Forecast | Starts **v0.3**, not v0.1 |
| Stack | Python pipelines + PostgreSQL + FastAPI + web dashboard |
| LLM role | Optional extract / classify / explain — not the forecast brain |
| License | MIT |
| Public | Yes from day one |

## Defense / sensitive domains

Public **analytical** modules only (macro trends, open sources).  
No operational guidance for targeting or violence. Adapters stay on open data and explicit non-goals.

## Success ladder

1. **v0.1** — ingest → state → signal → dashboard with evidence links  
2. **v0.4** — historical replay + blind forecast + evaluation metrics  
3. **v1.0** — generic core + adapters + SDK + API + web platform  
4. **Enterprise** — multi-tenant, SSO, SLAs, governance, scale, commercial packaging  

Detail: [ROADMAP.md](ROADMAP.md)
