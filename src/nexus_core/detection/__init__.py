"""State, signal, and anomaly detection (Phase 5)."""

from nexus_core.detection.anomaly import annotate_anomaly, severity_from_ratio
from nexus_core.detection.export import build_live_snapshot, write_live_snapshot
from nexus_core.detection.signals import detect_signals
from nexus_core.detection.state import compute_state_snapshots
from nexus_core.detection.store import persist_signals, persist_states

__all__ = [
    "annotate_anomaly",
    "build_live_snapshot",
    "compute_state_snapshots",
    "detect_signals",
    "persist_signals",
    "persist_states",
    "severity_from_ratio",
    "write_live_snapshot",
]
