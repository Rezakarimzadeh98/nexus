from __future__ import annotations

import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from nexus_core.ids import utc_now
from nexus_core.types import Forecast, ForecastQuestion


def hazard_probability(*, rate_per_hour: float, horizon_hours: float) -> float:
    """P(at least one event in horizon) under a constant Poisson hazard rate."""
    if rate_per_hour <= 0 or horizon_hours <= 0:
        return 0.0
    # Cap to avoid float underflow / overconfidence on tiny samples.
    p = 1.0 - math.exp(-rate_per_hour * horizon_hours)
    return max(0.0, min(p, 0.95))


def _confidence_from_samples(n: int) -> float:
    if n <= 0:
        return 0.2
    if n < 5:
        return 0.35
    if n < 15:
        return 0.55
    if n < 40:
        return 0.7
    return 0.82


def build_forecasts(
    events: list[tuple[UUID, str, datetime | None, list[UUID] | None]],
    *,
    horizon_hours: float = 72.0,
    lookback_hours: float = 24.0 * 14,
    top_k: int = 5,
    model_id: str = "hazard_rate_v1",
) -> list[Forecast]:
    """Baseline forecasts: will event type T recur within the horizon?"""
    now = utc_now()
    lookback_cut = now - timedelta(hours=lookback_hours)
    by_type: dict[str, list[tuple[UUID, datetime, list[UUID]]]] = defaultdict(list)

    for eid, etype, occurred, obs_ids in events:
        if not etype:
            continue
        ts = occurred or now
        if ts < lookback_cut:
            continue
        by_type[etype].append((eid, ts, list(obs_ids or [])))

    if not by_type:
        return []

    # Prefer frequent recent types
    ranked = sorted(by_type.items(), key=lambda kv: len(kv[1]), reverse=True)[:top_k]
    forecasts: list[Forecast] = []
    window_hours = max(lookback_hours, 1.0)

    for etype, rows in ranked:
        count = len(rows)
        rate = count / window_hours
        probability = hazard_probability(rate_per_hour=rate, horizon_hours=horizon_hours)
        confidence = _confidence_from_samples(count)
        evidence_events = [r[0] for r in rows[-5:]]
        evidence_obs: list[UUID] = []
        for _, _, obs in rows[-5:]:
            evidence_obs.extend(obs[:2])
        # unique preserve order
        seen: set[UUID] = set()
        uniq_obs: list[UUID] = []
        for oid in evidence_obs:
            if oid not in seen:
                seen.add(oid)
                uniq_obs.append(oid)

        question = ForecastQuestion(
            kind="event_in_horizon",
            event_type=etype,
            horizon_hours=horizon_hours,
            scope_key=f"event_type:{etype}",
            text=(
                f"Will at least one '{etype}' event occur within the next "
                f"{horizon_hours:.0f} hours?"
            ),
        )
        forecasts.append(
            Forecast(
                question=question,
                probability=round(probability, 4),
                confidence=round(confidence, 4),
                horizon_hours=horizon_hours,
                model_id=model_id,
                evidence_event_ids=evidence_events,
                evidence_observation_ids=uniq_obs[:8],
                summary=(
                    f"Hazard-rate baseline from {count} '{etype}' events in the last "
                    f"{lookback_hours / 24:.0f} days. Probability only — not a sure claim."
                ),
                metadata={
                    "lookback_hours": lookback_hours,
                    "sample_count": count,
                    "rate_per_hour": round(rate, 6),
                    "method": "poisson_hazard",
                },
            )
        )
    return forecasts


def recent_type_counts(
    events: list[tuple[UUID, str, datetime | None, list[UUID] | None]],
    *,
    hours: float = 24.0,
) -> Counter[str]:
    now = utc_now()
    cut = now - timedelta(hours=hours)
    counts: Counter[str] = Counter()
    for _, etype, occurred, _ in events:
        ts = occurred or now
        if ts >= cut and etype:
            counts[etype] += 1
    return counts


def event_payload_stats(forecasts: list[Forecast]) -> dict[str, Any]:
    return {
        "forecast_count": len(forecasts),
        "model_ids": sorted({f.model_id for f in forecasts}),
        "avg_probability": (
            round(sum(f.probability for f in forecasts) / len(forecasts), 4) if forecasts else 0.0
        ),
    }
