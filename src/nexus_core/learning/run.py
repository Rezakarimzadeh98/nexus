from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_core.db.models import EventRow
from nexus_core.evaluation.replay import blind_forecast_protocol
from nexus_core.ids import utc_now
from nexus_core.learning.analysis import build_error_report
from nexus_core.learning.recalibrate import fit_calibration, save_calibration
from nexus_core.learning.store import OutcomeRecord, persist_outcomes


def run_learn(
    session: Session,
    *,
    horizon_hours: float = 72.0,
    calibration_path: Path | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    """Record outcomes from blind protocol, analyze errors, fit recalibration."""
    rows = list(
        session.execute(select(EventRow).order_by(EventRow.occurred_at.asc()).limit(3000)).scalars()
    )
    events: list[tuple[UUID, str, datetime | None, list[UUID] | None]] = [
        (row.id, row.type, row.occurred_at, row.observation_ids) for row in rows
    ]
    blind = blind_forecast_protocol(events, horizon_hours=horizon_hours)
    scored = list(blind.get("scored") or [])

    cutoff_raw = blind.get("cutoff")
    cutoff = datetime.fromisoformat(cutoff_raw) if isinstance(cutoff_raw, str) else None

    outcomes: list[OutcomeRecord] = []
    forecasts = {f.get("question", {}).get("event_type"): f for f in blind.get("forecasts") or []}
    for row in scored:
        et = str(row.get("event_type") or "")
        fc = forecasts.get(et) or {}
        fc_id = fc.get("id")
        outcomes.append(
            OutcomeRecord(
                forecast_id=UUID(fc_id) if fc_id else None,
                event_type=et,
                probability=float(row.get("probability") or 0.0),
                outcome=int(row.get("outcome") or 0),
                horizon_hours=float(row.get("horizon_hours") or horizon_hours),
                cutoff=cutoff,
                metadata={"source": "blind_forecast_protocol"},
            )
        )

    if persist and outcomes:
        persist_outcomes(session, outcomes)

    report = build_error_report(scored)
    calibration = fit_calibration(scored)
    path = save_calibration(calibration, calibration_path)

    return {
        "generated_at": utc_now().isoformat(),
        "outcomes_recorded": len(outcomes),
        "error_report": report,
        "calibration": calibration,
        "calibration_path": str(path),
        "blind_brier": blind.get("brier_score"),
        "notes": (
            "Calibration is a simple mean-ratio affine map — "
            "a retrain hook, not a full model rebuild."
        ),
    }
