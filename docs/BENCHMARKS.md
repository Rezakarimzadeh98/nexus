# Public benchmarks

NEXUS publishes scorecards so the proof question is answered with numbers.

## Definition

See [`benchmarks/definitions/v1.yaml`](../benchmarks/definitions/v1.yaml).

Protocol highlights:

1. **Blind forecast** — train/forecast using only events at or before cutoff `T`, score outcomes in `(T, T+72h]`.
2. **Brier score** — lower is better; compared to a naive constant-0.5 baseline.
3. **Signal detection** — precision / recall / F1 / false-positive rate against velocity-proxy change labels.
4. **Lead time** — mean hours that a signal precedes a labeled change (when matched).

Change labels are **velocity-based proxies** for the public demo — not human-curated ground truth. Treat them as a reproducible baseline, not a final claim of superiority.

## How to run

```bash
alembic upgrade head
python -m nexus_core.cli ingest --sources adapters/generic/sources.yaml
python -m nexus_core.cli extract
python -m nexus_core.cli detect
python -m nexus_core.cli evaluate
# or
python benchmarks/run_baseline.py
```

## Latest published snapshot

Numbers refresh on each live ingest / evaluate export. Check the live demo evaluation panel or `status.json` → `evaluation`.

| Metric | Meaning |
| --- | --- |
| `brier_score` | Forecast calibration (↓ better) |
| `naive_brier_score` | Constant 0.5 reference |
| `brier_improvement_vs_naive` | naive − model (↑ better) |
| `signal_classification.f1` | Proxy change detection |
| `false_positive_rate` | FP / (FP+TN) |
| `detection_lead.mean_lead_hours` | Average early warning when matched |

Maintainer: [Reza Karimzadeh](https://github.com/Rezakarimzadeh98)
