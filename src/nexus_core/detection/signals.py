from __future__ import annotations

from datetime import timedelta

from nexus_core.detection.anomaly import annotate_anomaly
from nexus_core.ids import utc_now
from nexus_core.types import EvidenceRef, Observation, Signal, StateSnapshot


def _evidence_for_scope(
    observations: list[Observation],
    scope_key: str,
    *,
    limit: int = 5,
) -> list[EvidenceRef]:
    now = utc_now()
    cut = now - timedelta(hours=24)
    rows = observations
    if scope_key.startswith("source:"):
        source_id = scope_key.removeprefix("source:")
        rows = [o for o in observations if o.source_id == source_id]

    recent = []
    for obs in rows:
        ts = obs.published_at or obs.fetched_at
        if ts is not None and ts >= cut:
            recent.append(obs)
    recent.sort(key=lambda o: o.published_at or o.fetched_at, reverse=True)

    evidence: list[EvidenceRef] = []
    for obs in recent[:limit]:
        note = obs.title or obs.url or obs.source_id
        evidence.append(EvidenceRef(observation_id=obs.id, note=note, weight=1.0))
    return evidence


def detect_signals(
    snapshots: list[StateSnapshot],
    observations: list[Observation],
    *,
    velocity_threshold: float = 1.5,
    min_short_volume: float = 2.0,
) -> list[Signal]:
    """Emit What-Changed signals when short-window velocity exceeds baseline."""
    signals: list[Signal] = []
    for snap in snapshots:
        velocity = snap.metrics.get("velocity", 0.0)
        volume_short = snap.metrics.get("volume_short", 0.0)
        if volume_short < min_short_volume:
            continue
        if velocity < velocity_threshold:
            continue

        label = snap.scope_key
        title = f"Activity rise in {label}"
        change_ratio = velocity
        confidence = min(0.95, 0.45 + 0.1 * min(velocity, 5.0))

        signal = Signal(
            scope_key=snap.scope_key,
            title=title,
            change_ratio=change_ratio,
            confidence=round(confidence, 3),
            evidence=_evidence_for_scope(observations, snap.scope_key),
            metadata={
                "metrics": snap.metrics,
                "state_snapshot_id": str(snap.id),
            },
        )
        signals.append(annotate_anomaly(signal))
    signals.sort(key=lambda s: s.change_ratio or 0.0, reverse=True)
    return signals
