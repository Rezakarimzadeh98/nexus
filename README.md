# NEXUS

**Universal intelligence engine** — turn scattered data into a living model of what changed, why it matters, and what may happen next — then score those claims against reality.

[Product lock](docs/PRODUCT.md) · [Roadmap to enterprise](docs/ROADMAP.md) · [Architecture](docs/ARCHITECTURE.md)

> Status: **Phase 0 complete** � next **Phase 1 � Foundation**. Not a production intelligence platform yet.

## Why

Humans cannot jointly read millions of heterogeneous updates. Counting dashboards miss context; chatbots skip state, evidence, and evaluation. NEXUS is built as structured intelligence engines with a measurable proof question — see [PRODUCT.md](docs/PRODUCT.md).

## Roadmap (compressed)

| Phase | Outcome |
| --- | --- |
| 0 | Docs + public repo |
| 1 | Foundation (Compose, CI, types) |
| 2–3 | Ingest + normalize |
| 4–5 | Entity/event + **state/signal/anomaly** |
| 6 | Dashboard v0.1 (**What Changed**) |
| 7–8 | Graph/patterns + forecast/scenarios |
| 9–10 | Evaluation + feedback learning |
| 11 | v1.0 adapters + SDK + API platform |
| 12 | Enterprise (tenancy, SSO, SLA, scale) |

Full checklists: [docs/ROADMAP.md](docs/ROADMAP.md).

## Repository layout (target)

```text
nexus/
├── core/           # engines (ingestion → feedback)
├── adapters/       # generic, finance, cyber, …
├── models/         # trained/baseline artifacts
├── pipelines/      # orchestration
├── api/            # FastAPI
├── dashboard/      # web UI
├── datasets/       # fixtures / sample public extracts
├── benchmarks/     # evaluation definitions
├── experiments/
├── tests/
├── docs/
└── infrastructure/ # compose, later helm
```

## Non-goals (early)

- Operational military targeting
- “LLM → answer” as the product
- Claiming certain futures

## License

MIT © Reza Karimzadeh
