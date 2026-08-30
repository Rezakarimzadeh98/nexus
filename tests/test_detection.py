from __future__ import annotations

from datetime import timedelta

from nexus_core.detection.anomaly import severity_from_ratio
from nexus_core.detection.signals import detect_signals
from nexus_core.detection.state import compute_state_snapshots
from nexus_core.ids import utc_now
from nexus_core.types import Observation, SignalSeverity


def _obs(source: str, hours_ago: float, title: str) -> Observation:
    now = utc_now()
    ts = now - timedelta(hours=hours_ago)
    return Observation(
        source_id=source,
        title=title,
        body=title,
        published_at=ts,
        fetched_at=ts,
    )


def test_severity_bands() -> None:
    assert severity_from_ratio(1.2) == SignalSeverity.LOW
    assert severity_from_ratio(1.8) == SignalSeverity.MEDIUM
    assert severity_from_ratio(3.0) == SignalSeverity.HIGH
    assert severity_from_ratio(5.0) == SignalSeverity.CRITICAL


def test_state_and_signal_spike() -> None:
    # Quiet baseline days 2–6, then a burst in the last day.
    observations: list[Observation] = []
    for day in range(2, 7):
        observations.append(_obs("alpha", hours_ago=24 * day, title=f"quiet-{day}"))
    for i in range(8):
        observations.append(_obs("alpha", hours_ago=i * 0.5, title=f"spike-{i}"))

    snapshots = compute_state_snapshots(observations)
    by_scope = {s.scope_key: s for s in snapshots}
    assert "global" in by_scope
    assert "source:alpha" in by_scope
    assert by_scope["source:alpha"].metrics["volume_short"] >= 8

    signals = detect_signals(snapshots, observations, velocity_threshold=1.5, min_short_volume=2)
    assert signals
    top = signals[0]
    assert top.change_ratio is not None and top.change_ratio >= 1.5
    assert top.evidence
    assert top.metadata.get("why")
