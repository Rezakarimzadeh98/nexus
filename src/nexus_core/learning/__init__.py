"""Learning loop: outcomes, error analysis, recalibration (Phase 10)."""

from nexus_core.learning.analysis import build_error_report
from nexus_core.learning.recalibrate import (
    apply_calibration,
    fit_calibration,
    load_calibration,
    save_calibration,
)
from nexus_core.learning.store import persist_outcomes

__all__ = [
    "apply_calibration",
    "build_error_report",
    "fit_calibration",
    "load_calibration",
    "persist_outcomes",
    "run_learn",
    "save_calibration",
]


def __getattr__(name: str) -> object:
    if name == "run_learn":
        from nexus_core.learning.run import run_learn

        return run_learn
    raise AttributeError(name)
