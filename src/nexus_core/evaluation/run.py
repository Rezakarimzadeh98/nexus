from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_core.db.models import EventRow, ObservationRow, SignalRow
from nexus_core.evaluation.metrics import (
    brier_score,
    detection_lead_hours,
    false_positive_rate,
    precision_recall_f1,
)
from nexus_core.evaluation.replay import blind_forecast_protocol
from nexus_core.ids import utc_now


def _pseudo_change_labels(
    observations: list[tuple[datetime, str]],
    *,
    short_hours: float = 24.0,
    baseline_days: float = 7.0,
    velocity_threshold: float = 1.5,
) -> list[datetime]:
    """Label high-velocity source bursts as changes (benchmark proxy labels)."""
    now = utc_now()
    by_source: dict[str, list[datetime]] = defaultdict(list)
    for ts, source_id in observations:
        by_source[source_id].append(ts)

    changes: list[datetime] = []
    short_cut = now - timedelta(hours=short_hours)
    base_cut = now - timedelta(days=baseline_days)
    for _source, times in by_source.items():
        short_n = sum(1 for t in times if t >= short_cut)
        base_n = sum(1 for t in times if t >= base_cut)
        baseline_daily = base_n / max(baseline_days, 1.0)
        velocity = short_n / max(baseline_daily, 0.5)
        if short_n >= 2 and velocity >= velocity_threshold:
            recent = [t for t in times if t >= short_cut]
            if recent:
                changes.append(min(recent))
    return sorted(changes)


def run_evaluation(
    session: Session,
    *,
    horizon_hours: float = 72.0,
) -> dict[str, Any]:
    """Compute public evaluation scorecard from current DB history."""
    event_rows = list(
        session.execute(select(EventRow).order_by(EventRow.occurred_at.asc()).limit(3000)).scalars()
    )
    events: list[tuple[UUID, str, datetime | None, list[UUID] | None]] = [
        (row.id, row.type, row.occurred_at, row.observation_ids) for row in event_rows
    ]

    blind = blind_forecast_protocol(events, horizon_hours=horizon_hours)

    obs_rows = list(
        session.execute(
            select(ObservationRow).order_by(ObservationRow.fetched_at.asc()).limit(3000)
        ).scalars()
    )
    obs_points = [(row.fetched_at, row.source_id) for row in obs_rows if row.fetched_at]
    change_times = _pseudo_change_labels(obs_points)

    signal_rows = list(
        session.execute(select(SignalRow).order_by(SignalRow.detected_at.asc()).limit(500)).scalars()
    )
    signal_times = [row.detected_at for row in signal_rows if row.detected_at]

    # Signal vs change windows: predict change if any signal in prior 24h of change day buckets
    # Simpler binary frames: for each change, did we signal? + random negatives from quiet hours
    y_true: list[int] = []
    y_pred: list[int] = []
    for change in change_times:
        y_true.append(1)
        predicted = any(
            0 <= (change - sig).total_seconds() / 3600.0 <= 24.0 for sig in signal_times
        )
        y_pred.append(1 if predicted else 0)

    # Negatives: sample quiet timestamps (no change nearby)
    now = utc_now()
    for i in range(max(len(change_times), 3)):
        quiet = now - timedelta(hours=12 + i * 30)
        near_change = any(
            abs((quiet - c).total_seconds()) / 3600.0 < 12.0 for c in change_times
        )
        if near_change:
            continue
        y_true.append(0)
        predicted = any(
            0 <= (quiet - sig).total_seconds() / 3600.0 <= 24.0 for sig in signal_times
        )
        y_pred.append(1 if predicted else 0)

    clf = precision_recall_f1(y_true, y_pred) if y_true else {
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
        "tp": 0.0,
        "fp": 0.0,
        "fn": 0.0,
        "tn": 0.0,
    }
    fpr = false_positive_rate(int(clf["fp"]), int(clf["tn"]))
    lead = detection_lead_hours(signal_times, change_times)

    # Naive baseline: always predict no-change → Brier uses forecast blind score;
    # naive always-0.5 Brier for comparison when we have scored forecasts
    scored = blind.get("scored") or []
    naive_probs = [0.5] * len(scored)
    naive_outcomes = [int(s["outcome"]) for s in scored]
    naive_brier = brier_score(naive_probs, naive_outcomes) if scored else None

    return {
        "generated_at": now.isoformat(),
        "blind_forecast": blind,
        "signal_classification": clf,
        "false_positive_rate": fpr,
        "detection_lead": lead,
        "brier_score": blind.get("brier_score"),
        "naive_brier_score": naive_brier,
        "brier_improvement_vs_naive": (
            round((naive_brier or 0) - (blind.get("brier_score") or 0), 6)
            if naive_brier is not None and blind.get("brier_score") is not None
            else None
        ),
        "labels": {
            "change_events": len(change_times),
            "signals": len(signal_times),
            "frames": len(y_true),
        },
        "notes": (
            "Change labels are velocity-based proxies for public benchmarks — "
            "not human-curated ground truth."
        ),
    }
