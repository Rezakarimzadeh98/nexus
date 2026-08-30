from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_core.db.models import EventRow, StateSnapshotRow
from nexus_core.forecast.engine import build_forecasts
from nexus_core.forecast.scenarios import build_scenarios
from nexus_core.forecast.store import persist_forecasts


def run_forecast(
    session: Session,
    *,
    horizon_hours: float = 72.0,
    persist: bool = True,
    pattern_match_types: set[str] | None = None,
) -> dict[str, Any]:
    """Produce baseline forecasts + scenarios from event history."""
    rows = list(
        session.execute(select(EventRow).order_by(EventRow.occurred_at.asc()).limit(2000)).scalars()
    )
    events: list[tuple[UUID, str, datetime | None, list[UUID] | None]] = [
        (row.id, row.type, row.occurred_at, row.observation_ids) for row in rows
    ]
    forecasts = build_forecasts(events, horizon_hours=horizon_hours, top_k=5)

    velocity = 1.0
    snap = session.execute(
        select(StateSnapshotRow)
        .where(StateSnapshotRow.scope_key == "global")
        .order_by(StateSnapshotRow.captured_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    if snap and snap.metrics:
        velocity = float(snap.metrics.get("velocity", 1.0))

    matched = pattern_match_types or set()
    for forecast in forecasts:
        boost = 1.0 if forecast.question.event_type in matched else 0.0
        forecast.scenarios = build_scenarios(
            forecast, velocity=velocity, pattern_boost=boost
        )
        # Keep scenario probabilities normalized (float round may drift).
        total = sum(s.probability for s in forecast.scenarios) or 1.0
        for scenario in forecast.scenarios:
            scenario.probability = round(scenario.probability / total, 4)

    if persist and forecasts:
        persist_forecasts(session, forecasts)

    return {
        "forecasts": [f.model_dump(mode="json") for f in forecasts],
        "counts": {"forecasts": len(forecasts)},
    }
