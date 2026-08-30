from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from nexus_core import __version__
from nexus_core.db.models import (
    EntityRow,
    EventRow,
    ObservationRow,
    RelationRow,
    SignalRow,
    StateSnapshotRow,
)
from nexus_core.ids import utc_now
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
) -> dict[str, Any]:
    """JSON payload for the public live demo / Pages site."""
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
    }

    recent_rows = session.execute(
        select(ObservationRow).order_by(ObservationRow.fetched_at.desc()).limit(recent_limit)
    ).scalars()
    recent = [_obs_public(r) for r in recent_rows]

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
        "proof_question": (
            "Can heterogeneous public data become a living model that detects "
            "important change with evidence?"
        ),
        "counts": counts,
        "states": state_payload,
        "signals": signal_payload,
        "recent_observations": recent,
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
