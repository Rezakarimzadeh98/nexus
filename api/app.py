"""NEXUS HTTP API — What Changed + platform jobs."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import select

from nexus_core import __version__
from nexus_core.adapters import get_adapter, list_adapters
from nexus_core.auth import require_api_key
from nexus_core.config import get_settings
from nexus_core.db import make_engine, make_session_factory, ping_database
from nexus_core.db.models import ObservationRow, SignalRow, StateSnapshotRow
from nexus_core.ingestion import ingest_many

MAINTAINER = {
    "name": "Reza Karimzadeh",
    "github": "https://github.com/Rezakarimzadeh98",
    "repo": "https://github.com/Rezakarimzadeh98/nexus",
}

TAGS_METADATA = [
    {"name": "meta", "description": "Health and service metadata"},
    {"name": "live", "description": "Public live snapshot"},
    {"name": "signals", "description": "What Changed signals"},
    {"name": "state", "description": "Living state snapshots"},
    {"name": "observations", "description": "Normalized observations"},
    {"name": "discovery", "description": "Graph and patterns"},
    {"name": "forecasts", "description": "Probabilistic forecasts"},
    {"name": "evaluation", "description": "Scorecards"},
    {"name": "learning", "description": "Outcomes and calibration"},
    {"name": "adapters", "description": "Domain adapters"},
    {"name": "jobs", "description": "Authenticated write / pipeline jobs"},
]

app = FastAPI(
    title="NEXUS API",
    description=(
        "Universal Intelligence Engine — state, signals, evidence, forecasts. "
        "Maintained by Reza Karimzadeh (https://github.com/Rezakarimzadeh98). "
        "Write paths require `Authorization: Bearer <NEXUS_API_KEY>` when configured."
    ),
    version=__version__,
    contact={
        "name": "Reza Karimzadeh",
        "url": "https://github.com/Rezakarimzadeh98",
        "email": "r.karimzadeh1998@gmail.com",
    },
    openapi_tags=TAGS_METADATA,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class IngestJobRequest(BaseModel):
    adapter: str = Field(default="generic")
    offline: bool = Field(default=True, description="Use sources.ci.yaml fixtures")
    dry_run: bool = Field(default=True)
    fixture_root: str = Field(default="datasets")
    source_id: str | None = None


class DetectJobRequest(BaseModel):
    limit: int = Field(default=500, ge=1, le=5000)
    velocity_threshold: float = Field(default=1.5, gt=0)
    min_short_volume: float = Field(default=2.0, ge=0)


def _snapshot_path() -> Path | None:
    raw = os.environ.get("NEXUS_SNAPSHOT_PATH") or get_settings().snapshot_path
    path = Path(raw)
    return path if path.is_file() else None


def _load_snapshot() -> dict[str, Any] | None:
    path = _snapshot_path()
    if path is None:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/", tags=["meta"])
def root() -> dict[str, Any]:
    return {
        "name": "NEXUS",
        "version": __version__,
        "maintainer": MAINTAINER,
        "demo": "https://rezakarimzadeh98.github.io/nexus/",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "ui": "/ui/",
        "site": "/site/",
        "portal": "/portal/",
    }


@app.get("/health", tags=["meta"])
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
        "auth_required_for_writes": bool(get_settings().api_key),
        "maintainer": MAINTAINER,
    }


@app.get("/live", tags=["live"])
def live() -> dict[str, Any]:
    snap = _load_snapshot()
    if snap is None:
        raise HTTPException(status_code=404, detail="No live snapshot yet")
    return snap


@app.get("/signals", tags=["signals"])
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


@app.get("/signals/{signal_id}", tags=["signals"])
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


@app.get("/state/{scope_key:path}", tags=["state"])
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


@app.get("/observations/{observation_id}", tags=["observations"])
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


@app.get("/patterns", tags=["discovery"])
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


@app.get("/graph/neighborhood", tags=["discovery"])
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


@app.get("/forecasts", tags=["forecasts"])
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


@app.get("/forecasts/{forecast_id}", tags=["forecasts"])
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


@app.get("/evaluation", tags=["evaluation"])
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


@app.get("/learning", tags=["learning"])
def get_learning() -> dict[str, Any]:
    try:
        from sqlalchemy import func

        from nexus_core.db.models import OutcomeRow
        from nexus_core.learning.recalibrate import load_calibration

        engine = make_engine(get_settings())
        factory = make_session_factory(engine)
        with factory() as session:
            n = session.execute(select(func.count()).select_from(OutcomeRow)).scalar_one()
        return {
            "outcomes": n,
            "calibration": load_calibration(),
            "notes": "Affine recalibration from recorded blind-protocol outcomes.",
        }
    except Exception:
        snap = _load_snapshot()
        if snap is None or "learning" not in snap:
            raise HTTPException(status_code=503, detail="Unavailable") from None
        return snap["learning"]


@app.get("/v1/adapters", tags=["adapters"])
def adapters_list() -> list[dict[str, Any]]:
    return [a.as_dict() for a in list_adapters()]


@app.get("/v1/adapters/{domain}", tags=["adapters"])
def adapters_get(domain: str) -> dict[str, Any]:
    try:
        return get_adapter(domain).as_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/v1/jobs/ingest", tags=["jobs"])
def job_ingest(
    body: IngestJobRequest,
    _: Annotated[str | None, Depends(require_api_key)] = None,
) -> dict[str, Any]:
    try:
        adapter = get_adapter(body.adapter)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None

    sources = adapter.load_source_configs(offline=body.offline)
    if body.source_id:
        sources = [s for s in sources if s.id == body.source_id]
    fixture_root = Path(body.fixture_root)

    if body.dry_run:
        results = ingest_many(None, sources, fixture_root=fixture_root, persist=False)
    else:
        engine = make_engine(get_settings())
        factory = make_session_factory(engine)
        with factory() as session:
            results = ingest_many(session, sources, fixture_root=fixture_root, persist=True)
            session.commit()

    return {
        "adapter": body.adapter,
        "dry_run": body.dry_run,
        "offline": body.offline,
        "results": [
            {
                "source_id": r.source_id,
                "fetched": r.fetched,
                "observation_count": r.observation_count,
                "inserted": r.inserted,
                "error": r.error,
            }
            for r in results
        ],
    }


@app.post("/v1/jobs/detect", tags=["jobs"])
def job_detect(
    body: DetectJobRequest,
    _: Annotated[str | None, Depends(require_api_key)] = None,
) -> dict[str, Any]:
    from nexus_core.detection import (
        compute_state_snapshots,
        detect_signals,
        persist_signals,
        persist_states,
    )
    from nexus_core.detection.export import observations_from_rows

    engine = make_engine(get_settings())
    factory = make_session_factory(engine)
    with factory() as session:
        rows = session.execute(
            select(ObservationRow).order_by(ObservationRow.fetched_at.desc()).limit(body.limit)
        ).scalars().all()
        observations = observations_from_rows(rows)
        states = compute_state_snapshots(observations)
        signals = detect_signals(
            states,
            observations,
            velocity_threshold=body.velocity_threshold,
            min_short_volume=body.min_short_volume,
        )
        persist_states(session, states)
        persist_signals(session, signals)
        session.commit()
    return {
        "observations": len(observations),
        "states": len(states),
        "signals": len(signals),
    }


@app.get("/ui/status.json", tags=["live"])
def ui_status() -> FileResponse:
    path = _snapshot_path()
    if path is None:
        raise HTTPException(status_code=404, detail="No live snapshot yet")
    return FileResponse(path, media_type="application/json")


_ROOT = Path(__file__).resolve().parents[1]
_DASHBOARD_DIR = _ROOT / "dashboard"
_SITE_DIR = _ROOT / "site"
_PORTAL_DIR = _ROOT / "docs" / "portal"

if _DASHBOARD_DIR.is_dir():
    app.mount("/ui", StaticFiles(directory=str(_DASHBOARD_DIR), html=True), name="ui")
if _SITE_DIR.is_dir():
    app.mount("/site", StaticFiles(directory=str(_SITE_DIR), html=True), name="site")
if _PORTAL_DIR.is_dir():
    app.mount("/portal", StaticFiles(directory=str(_PORTAL_DIR), html=True), name="portal")
