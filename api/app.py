"""NEXUS HTTP API — What Changed."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from nexus_core import __version__
from nexus_core.config import get_settings
from nexus_core.db import make_engine, make_session_factory, ping_database
from nexus_core.db.models import ObservationRow, SignalRow, StateSnapshotRow

MAINTAINER = {
    "name": "Reza Karimzadeh",
    "github": "https://github.com/Rezakarimzadeh98",
    "repo": "https://github.com/Rezakarimzadeh98/nexus",
}

app = FastAPI(
    title="NEXUS API",
    description=(
        "Universal Intelligence Engine — state, signals, evidence. "
        "Maintained by Reza Karimzadeh (https://github.com/Rezakarimzadeh98)."
    ),
    version=__version__,
    contact={
        "name": "Reza Karimzadeh",
        "url": "https://github.com/Rezakarimzadeh98",
        "email": "r.karimzadeh1998@gmail.com",
    },
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def _snapshot_path() -> Path | None:
    raw = os.environ.get("NEXUS_SNAPSHOT_PATH", "docs/live/status.json")
    path = Path(raw)
    return path if path.is_file() else None


def _load_snapshot() -> dict[str, Any] | None:
    path = _snapshot_path()
    if path is None:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/health")
def health() -> dict[str, Any]:
    db_ok = False
    try:
        db_ok = ping_database(make_engine(get_settings()))
    except Exception:
        db_ok = False
    return {
        "status": "ok" if db_ok or _snapshot_path() else "degraded",
        "version": __version__,
        "database": db_ok,
        "snapshot": _snapshot_path() is not None,
        "maintainer": MAINTAINER,
    }


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "name": "NEXUS",
        "version": __version__,
        "maintainer": MAINTAINER,
        "demo": "https://rezakarimzadeh98.github.io/nexus/",
        "docs": "/docs",
        "ui": "/ui/",
    }


@app.get("/live")
def live() -> dict[str, Any]:
    snap = _load_snapshot()
    if snap is None:
        raise HTTPException(status_code=404, detail="No live snapshot yet")
    return snap


@app.get("/signals")
def list_signals(limit: int = 20) -> list[dict[str, Any]]:
    limit = max(1, min(limit, 100))
    try:
        engine = make_engine(get_settings())
        factory = make_session_factory(engine)
        with factory() as session:
            rows = session.execute(
                select(SignalRow).order_by(SignalRow.detected_at.desc()).limit(limit)
            ).scalars()
            return [
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
                for r in rows
            ]
    except Exception:
        snap = _load_snapshot()
        if snap is None:
            raise HTTPException(
                status_code=503, detail="Database and snapshot unavailable"
            ) from None
        return list(snap.get("signals", []))[:limit]


@app.get("/signals/{signal_id}")
def get_signal(signal_id: UUID) -> dict[str, Any]:
    try:
        engine = make_engine(get_settings())
        factory = make_session_factory(engine)
        with factory() as session:
            row = session.get(SignalRow, signal_id)
            if row is None:
                raise HTTPException(status_code=404, detail="Signal not found")
            return {
                "id": str(row.id),
                "scope_key": row.scope_key,
                "title": row.title,
                "summary": row.summary,
                "severity": row.severity,
                "confidence": row.confidence,
                "change_ratio": row.change_ratio,
                "detected_at": row.detected_at.isoformat(),
                "evidence": row.evidence or [],
                "contradictions": row.contradictions or [],
                "metadata": row.metadata_json or {},
            }
    except HTTPException:
        raise
    except Exception:
        snap = _load_snapshot()
        if snap is None:
            raise HTTPException(status_code=503, detail="Unavailable") from None
        for item in snap.get("signals", []):
            if item.get("id") == str(signal_id):
                return item
        raise HTTPException(status_code=404, detail="Signal not found") from None


@app.get("/state/{scope_key:path}")
def get_state(scope_key: str) -> dict[str, Any]:
    try:
        engine = make_engine(get_settings())
        factory = make_session_factory(engine)
        with factory() as session:
            row = session.execute(
                select(StateSnapshotRow)
                .where(StateSnapshotRow.scope_key == scope_key)
                .order_by(StateSnapshotRow.captured_at.desc())
                .limit(1)
            ).scalar_one_or_none()
            if row is None:
                raise HTTPException(status_code=404, detail="State not found")
            return {
                "id": str(row.id),
                "scope_key": row.scope_key,
                "captured_at": row.captured_at.isoformat(),
                "metrics": row.metrics,
                "metadata": row.metadata_json or {},
            }
    except HTTPException:
        raise
    except Exception:
        snap = _load_snapshot()
        if snap is None:
            raise HTTPException(status_code=503, detail="Unavailable") from None
        for item in snap.get("states", []):
            if item.get("scope_key") == scope_key:
                return item
        raise HTTPException(status_code=404, detail="State not found") from None


@app.get("/observations/{observation_id}")
def get_observation(observation_id: UUID) -> dict[str, Any]:
    try:
        engine = make_engine(get_settings())
        factory = make_session_factory(engine)
        with factory() as session:
            row = session.get(ObservationRow, observation_id)
            if row is None:
                raise HTTPException(status_code=404, detail="Observation not found")
            return {
                "id": str(row.id),
                "source_id": row.source_id,
                "title": row.title,
                "body": row.body,
                "url": row.url,
                "published_at": row.published_at.isoformat() if row.published_at else None,
                "fetched_at": row.fetched_at.isoformat() if row.fetched_at else None,
                "language": row.language,
                "raw_hash": row.raw_hash,
                "metadata": row.metadata_json or {},
            }
    except HTTPException:
        raise
    except Exception:
        snap = _load_snapshot()
        if snap is None:
            raise HTTPException(status_code=503, detail="Unavailable") from None
        for item in snap.get("recent_observations", []):
            if item.get("id") == str(observation_id):
                return item
        raise HTTPException(status_code=404, detail="Observation not found") from None


@app.get("/patterns")
def list_patterns(limit: int = 20) -> list[dict[str, Any]]:
    limit = max(1, min(limit, 100))
    try:
        from nexus_core.db.models import PatternRow

        engine = make_engine(get_settings())
        factory = make_session_factory(engine)
        with factory() as session:
            rows = session.execute(select(PatternRow).limit(limit)).scalars().all()
            return [
                {
                    "id": str(r.id),
                    "sequence": r.sequence,
                    "support": r.support,
                    "confidence": r.confidence,
                    "count": r.count,
                    "example_event_ids": [str(x) for x in (r.example_event_ids or [])],
                    "metadata": r.metadata_json or {},
                }
                for r in rows
            ]
    except Exception:
        snap = _load_snapshot()
        if snap is None:
            raise HTTPException(status_code=503, detail="Unavailable") from None
        return list(snap.get("patterns", []))[:limit]


@app.get("/graph/neighborhood")
def graph_neighborhood(
    entity_id: UUID | None = None,
    canonical_key: str | None = None,
    depth: int = 1,
    limit: int = 48,
) -> dict[str, Any]:
    try:
        from nexus_core.discovery.graph import build_neighborhood

        engine = make_engine(get_settings())
        factory = make_session_factory(engine)
        with factory() as session:
            nb = build_neighborhood(
                session,
                entity_id=entity_id,
                canonical_key=canonical_key,
                depth=depth,
                limit=limit,
            )
            if nb is None:
                raise HTTPException(status_code=404, detail="No graph neighborhood")
            return nb.as_dict()
    except HTTPException:
        raise
    except Exception:
        snap = _load_snapshot()
        if snap is None:
            raise HTTPException(status_code=503, detail="Unavailable") from None
        graph = snap.get("graph")
        if not graph:
            raise HTTPException(status_code=404, detail="No graph neighborhood") from None
        return graph


@app.get("/forecasts")
def list_forecasts(limit: int = 20) -> list[dict[str, Any]]:
    limit = max(1, min(limit, 100))
    try:
        from nexus_core.db.models import ForecastRow

        engine = make_engine(get_settings())
        factory = make_session_factory(engine)
        with factory() as session:
            rows = (
                session.execute(
                    select(ForecastRow).order_by(ForecastRow.created_at.desc()).limit(limit)
                )
                .scalars()
                .all()
            )
            return [
                {
                    "id": str(r.id),
                    "question": r.question,
                    "probability": r.probability,
                    "confidence": r.confidence,
                    "horizon_hours": r.horizon_hours,
                    "model_id": r.model_id,
                    "created_at": r.created_at.isoformat(),
                    "scenarios": r.scenarios or [],
                    "summary": r.summary,
                    "evidence_event_ids": [str(x) for x in (r.evidence_event_ids or [])],
                    "metadata": r.metadata_json or {},
                }
                for r in rows
            ]
    except Exception:
        snap = _load_snapshot()
        if snap is None:
            raise HTTPException(status_code=503, detail="Unavailable") from None
        return list(snap.get("forecasts", []))[:limit]


@app.get("/forecasts/{forecast_id}")
def get_forecast(forecast_id: UUID) -> dict[str, Any]:
    try:
        from nexus_core.db.models import ForecastRow

        engine = make_engine(get_settings())
        factory = make_session_factory(engine)
        with factory() as session:
            row = session.get(ForecastRow, forecast_id)
            if row is None:
                raise HTTPException(status_code=404, detail="Forecast not found")
            return {
                "id": str(row.id),
                "question": row.question,
                "probability": row.probability,
                "confidence": row.confidence,
                "horizon_hours": row.horizon_hours,
                "model_id": row.model_id,
                "created_at": row.created_at.isoformat(),
                "scenarios": row.scenarios or [],
                "summary": row.summary,
                "evidence_event_ids": [str(x) for x in (row.evidence_event_ids or [])],
                "evidence_observation_ids": [
                    str(x) for x in (row.evidence_observation_ids or [])
                ],
                "metadata": row.metadata_json or {},
            }
    except HTTPException:
        raise
    except Exception:
        snap = _load_snapshot()
        if snap is None:
            raise HTTPException(status_code=503, detail="Unavailable") from None
        for item in snap.get("forecasts", []):
            if item.get("id") == str(forecast_id):
                return item
        raise HTTPException(status_code=404, detail="Forecast not found") from None


@app.get("/evaluation")
def get_evaluation() -> dict[str, Any]:
    try:
        from nexus_core.evaluation import run_evaluation

        engine = make_engine(get_settings())
        factory = make_session_factory(engine)
        with factory() as session:
            return run_evaluation(session, horizon_hours=72.0)
    except Exception:
        snap = _load_snapshot()
        if snap is None or "evaluation" not in snap:
            raise HTTPException(status_code=503, detail="Unavailable") from None
        return snap["evaluation"]


@app.get("/ui/status.json")
def ui_status() -> FileResponse:
    path = _snapshot_path()
    if path is None:
        raise HTTPException(status_code=404, detail="No live snapshot yet")
    return FileResponse(path, media_type="application/json")


_DASHBOARD_DIR = Path(__file__).resolve().parents[1] / "dashboard"
if _DASHBOARD_DIR.is_dir():
    app.mount("/ui", StaticFiles(directory=str(_DASHBOARD_DIR), html=True), name="ui")
