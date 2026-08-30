from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from nexus_core.evaluation.metrics import brier_score
from nexus_core.forecast.engine import build_forecasts
from nexus_core.forecast.scenarios import build_scenarios
from nexus_core.ids import utc_now


def filter_before(
    events: list[tuple[UUID, str, datetime | None, list[UUID] | None]],
    cutoff: datetime,
) -> list[tuple[UUID, str, datetime | None, list[UUID] | None]]:
    """Time-travel cutoff: keep only events at or before cutoff."""
    kept: list[tuple[UUID, str, datetime | None, list[UUID] | None]] = []
    for item in events:
        ts = item[2]
        if ts is None or ts <= cutoff:
            kept.append(item)
    return kept


def events_in_window(
    events: list[tuple[UUID, str, datetime | None, list[UUID] | None]],
    start: datetime,
    end: datetime,
) -> list[tuple[UUID, str, datetime | None, list[UUID] | None]]:
    out: list[tuple[UUID, str, datetime | None, list[UUID] | None]] = []
    for item in events:
        ts = item[2]
        if ts is not None and start < ts <= end:
            out.append(item)
    return out


def blind_forecast_protocol(
    events: list[tuple[UUID, str, datetime | None, list[UUID] | None]],
    *,
    cutoff: datetime | None = None,
    horizon_hours: float = 72.0,
    lookback_hours: float = 24.0 * 14,
) -> dict[str, Any]:
    """
    Blind protocol: forecast using only pre-cutoff history, score on post-cutoff outcomes.
    """
    now = utc_now()
    cut = cutoff or (now - timedelta(hours=horizon_hours))
    horizon_end = cut + timedelta(hours=horizon_hours)

    past = filter_before(events, cut)
    future = events_in_window(events, cut, horizon_end)

    forecasts = build_forecasts(
        past,
        horizon_hours=horizon_hours,
        lookback_hours=lookback_hours,
        top_k=5,
    )
    for fc in forecasts:
        fc.scenarios = build_scenarios(fc, velocity=1.0, pattern_boost=0.0)

    future_types = {item[1] for item in future}
    probs: list[float] = []
    outcomes: list[int] = []
    details: list[dict[str, Any]] = []
    for fc in forecasts:
        y = 1 if fc.question.event_type in future_types else 0
        probs.append(fc.probability)
        outcomes.append(y)
        details.append(
            {
                "event_type": fc.question.event_type,
                "probability": fc.probability,
                "outcome": y,
                "horizon_hours": horizon_hours,
            }
        )

    return {
        "cutoff": cut.isoformat(),
        "horizon_hours": horizon_hours,
        "horizon_end": horizon_end.isoformat(),
        "past_events": len(past),
        "future_events": len(future),
        "forecasts": [f.model_dump(mode="json") for f in forecasts],
        "scored": details,
        "brier_score": brier_score(probs, outcomes) if probs else None,
        "n_scored": len(probs),
    }
