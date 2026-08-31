from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from nexus_core import __version__
from nexus_core.adapters import list_adapters
from nexus_core.db.models import (
    EntityRow,
    EventRow,
    ForecastRow,
    ObservationRow,
    OutcomeRow,
    PatternRow,
    RelationRow,
    SignalRow,
    StateSnapshotRow,
)
from nexus_core.discovery.run import run_discovery
from nexus_core.evaluation.run import run_evaluation
from nexus_core.forecast.run import run_forecast
from nexus_core.ids import utc_now
from nexus_core.learning.recalibrate import load_calibration
from nexus_core.types import Observation, Signal, StateSnapshot


def _obs_public(row: ObservationRow) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "source_id": row.source_id,
        "title": row.title,
        "url": row.url,
        "published_at": row.published_at.isoformat() if row.published_at else None,
        "fetched_at": row.fetched_at.isoformat() if row.fetched_at else None,
    }


def build_live_snapshot(
    session: Session,
    *,
    snapshots: list[StateSnapshot] | None = None,
    signals: list[Signal] | None = None,
    recent_limit: int = 25,
    discovery: dict[str, Any] | None = None,
    forecast: dict[str, Any] | None = None,
    evaluation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """JSON payload for the public live demo / Pages site."""
    if discovery is None:
        discovery = run_discovery(session, persist=False)
    if forecast is None:
        matched = {
            (m.get("expected_next") or "")
            for m in discovery.get("pattern_matches", [])
            if isinstance(m, dict)
        }
        matched |= {
            seq[-1]
            for p in discovery.get("patterns", [])
            if isinstance(p, dict)
            for seq in [p.get("sequence") or []]
            if seq
        }
        forecast = run_forecast(
            session,
            persist=False,
            pattern_match_types={t for t in matched if t},
        )
    if evaluation is None:
        evaluation = run_evaluation(session, horizon_hours=72.0)
    counts = {
        "observations": session.execute(
            select(func.count()).select_from(ObservationRow)
        ).scalar_one(),
        "entities": session.execute(select(func.count()).select_from(EntityRow)).scalar_one(),
        "events": session.execute(select(func.count()).select_from(EventRow)).scalar_one(),
        "relations": session.execute(select(func.count()).select_from(RelationRow)).scalar_one(),
        "state_snapshots": session.execute(
            select(func.count()).select_from(StateSnapshotRow)
        ).scalar_one(),
        "signals": session.execute(select(func.count()).select_from(SignalRow)).scalar_one(),
        "patterns": session.execute(select(func.count()).select_from(PatternRow)).scalar_one(),
        "forecasts": session.execute(select(func.count()).select_from(ForecastRow)).scalar_one(),
        "outcomes": session.execute(select(func.count()).select_from(OutcomeRow)).scalar_one(),
    }

    recent_rows = list(
        session.execute(
            select(ObservationRow).order_by(ObservationRow.fetched_at.desc()).limit(recent_limit)
        ).scalars()
    )
    recent = [_obs_public(r) for r in recent_rows]
    obs_index = {item["id"]: item for item in recent}

    # Also index evidence observation ids that may fall outside the recent window.
    evidence_ids: set[str] = set()
    if signals is not None:
        for sig in signals:
            for ref in sig.evidence:
                evidence_ids.add(str(ref.observation_id))
    else:
        for row_sig in session.execute(
            select(SignalRow).order_by(SignalRow.detected_at.desc()).limit(20)
        ).scalars():
            for item in row_sig.evidence or []:
                oid = item.get("observation_id") if isinstance(item, dict) else None
                if oid:
                    evidence_ids.add(str(oid))

    missing = [oid for oid in evidence_ids if oid not in obs_index]
    if missing:
        for oid in missing[:50]:
            try:
                row = session.get(ObservationRow, UUID(oid))
            except ValueError:
                continue
            if row is not None:
                obs_index[str(row.id)] = _obs_public(row)

    state_payload = (
        [s.model_dump(mode="json") for s in snapshots]
        if snapshots is not None
        else [
            {
                "id": str(r.id),
                "scope_key": r.scope_key,
                "captured_at": r.captured_at.isoformat(),
                "metrics": r.metrics,
                "metadata": r.metadata_json or {},
            }
            for r in session.execute(
                select(StateSnapshotRow).order_by(StateSnapshotRow.captured_at.desc()).limit(20)
            ).scalars()
        ]
    )

    signal_payload = (
        [s.model_dump(mode="json") for s in signals]
        if signals is not None
        else [
            {
                "id": str(r.id),
                "scope_key": r.scope_key,
                "title": r.title,
                "summary": r.summary,
                "severity": r.severity,
                "confidence": r.confidence,
                "change_ratio": r.change_ratio,
                "detected_at": r.detected_at.isoformat(),
                "evidence": r.evidence or [],
                "metadata": r.metadata_json or {},
            }
            for r in session.execute(
                select(SignalRow).order_by(SignalRow.detected_at.desc()).limit(20)
            ).scalars()
        ]
    )

    return {
        "version": __version__,
        "generated_at": utc_now().isoformat(),
        "maintainer": {
            "name": "Reza Karimzadeh",
            "github": "https://github.com/Rezakarimzadeh98",
            "profile": "https://github.com/Rezakarimzadeh98",
            "repo": "https://github.com/Rezakarimzadeh98/nexus",
        },
        "platform": {
            "phase": "14",
            "status": "hardened",
            "adapters": [a.domain for a in list_adapters()],
            "features": [
                "live-state",
                "signals",
                "forecasts",
                "evaluation",
                "learning",
                "tenancy",
                "oidc-jwks",
                "job-workers",
            ],
            "links": {
                "docs": "https://github.com/Rezakarimzadeh98/nexus/tree/main/docs",
                "enterprise": (
                    "https://github.com/Rezakarimzadeh98/nexus/tree/main/docs/enterprise"
                ),
            },
        },
        "proof_question": (
            "Can heterogeneous public data become a living model that detects "
            "important change with evidence?"
        ),
        "counts": counts,
        "states": state_payload,
        "signals": signal_payload,
        "recent_observations": recent,
        "observations_by_id": obs_index,
        "graph": discovery.get("graph", {"nodes": [], "edges": []}),
        "patterns": discovery.get("patterns", []),
        "pattern_matches": discovery.get("pattern_matches", []),
        "forecasts": forecast.get("forecasts", []),
        "evaluation": {
            "brier_score": evaluation.get("brier_score"),
            "naive_brier_score": evaluation.get("naive_brier_score"),
            "brier_improvement_vs_naive": evaluation.get("brier_improvement_vs_naive"),
            "false_positive_rate": evaluation.get("false_positive_rate"),
            "signal_classification": evaluation.get("signal_classification"),
            "detection_lead": evaluation.get("detection_lead"),
            "labels": evaluation.get("labels"),
            "notes": evaluation.get("notes"),
            "blind_forecast": {
                "cutoff": (evaluation.get("blind_forecast") or {}).get("cutoff"),
                "horizon_hours": (evaluation.get("blind_forecast") or {}).get(
                    "horizon_hours"
                ),
                "n_scored": (evaluation.get("blind_forecast") or {}).get("n_scored"),
                "brier_score": (evaluation.get("blind_forecast") or {}).get("brier_score"),
            },
        },
        "learning": {
            "calibration": load_calibration(),
            "notes": (
                "Run `nexus learn` to record outcomes and refresh affine calibration "
                "applied by hazard_rate_v1."
            ),
        },
    }


def write_live_snapshot(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def observations_from_rows(rows: list[ObservationRow]) -> list[Observation]:
    return [
        Observation(
            id=row.id,
            source_id=row.source_id,
            title=row.title,
            body=row.body,
            url=row.url,
            published_at=row.published_at,
            fetched_at=row.fetched_at,
            language=row.language,
            raw_hash=row.raw_hash,
            raw_uri=row.raw_uri,
            metadata=row.metadata_json or {},
        )
        for row in rows
    ]
