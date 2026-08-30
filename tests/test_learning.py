from __future__ import annotations

from nexus_core.learning.analysis import build_error_report
from nexus_core.learning.recalibrate import apply_calibration, fit_calibration


def test_fit_and_apply_calibration() -> None:
    scored = [
        {"event_type": "A", "probability": 0.8, "outcome": 0},
        {"event_type": "A", "probability": 0.8, "outcome": 0},
        {"event_type": "B", "probability": 0.2, "outcome": 1},
        {"event_type": "B", "probability": 0.2, "outcome": 1},
    ]
    cal = fit_calibration(scored)
    assert cal["n"] == 4
    assert cal["a"] > 0
    p = apply_calibration(0.5, cal)
    assert 0.0 <= p <= 0.95


def test_error_report_flags() -> None:
    scored = [
        {"event_type": "X", "probability": 0.9, "outcome": 0},
        {"event_type": "Y", "probability": 0.1, "outcome": 1},
    ]
    report = build_error_report(scored)
    assert report["overconfident_count"] == 1
    assert report["underconfident_count"] == 1
    assert report["suggestions"]
