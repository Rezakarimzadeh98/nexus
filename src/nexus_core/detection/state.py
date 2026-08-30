from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

from nexus_core.ids import utc_now
from nexus_core.types import Observation, StateSnapshot


def compute_state_snapshots(
    observations: list[Observation],
    *,
    short_hours: float = 24.0,
    baseline_days: float = 7.0,
) -> list[StateSnapshot]:
    """Rolling volume/velocity/recency metrics for global and per-source scopes."""
    now = utc_now()
    short_cut = now - timedelta(hours=short_hours)
    base_cut = now - timedelta(days=baseline_days)

    by_scope: dict[str, list[Observation]] = defaultdict(list)
    for obs in observations:
        by_scope["global"].append(obs)
        by_scope[f"source:{obs.source_id}"].append(obs)

    snapshots: list[StateSnapshot] = []
    for scope_key, rows in sorted(by_scope.items()):
        short_n = 0
        base_n = 0
        newest_hours: float | None = None
        sources: set[str] = set()
        for obs in rows:
            ts = obs.published_at or obs.fetched_at
            if ts is None:
                continue
            if ts >= short_cut:
                short_n += 1
            if ts >= base_cut:
                base_n += 1
            age_h = (now - ts).total_seconds() / 3600.0
            if newest_hours is None or age_h < newest_hours:
                newest_hours = age_h
            sources.add(obs.source_id)

        baseline_daily = base_n / max(baseline_days, 1.0)
        velocity = short_n / max(baseline_daily, 0.5)

        snapshots.append(
            StateSnapshot(
                scope_key=scope_key,
                captured_at=now,
                metrics={
                    "volume_short": float(short_n),
                    "volume_baseline": float(base_n),
                    "baseline_daily": round(baseline_daily, 4),
                    "velocity": round(velocity, 4),
                    "recency_hours": round(newest_hours, 4) if newest_hours is not None else -1.0,
                    "source_diversity": float(len(sources)),
                    "observation_total": float(len(rows)),
                },
                metadata={
                    "short_hours": short_hours,
                    "baseline_days": baseline_days,
                },
            )
        )
    return snapshots
