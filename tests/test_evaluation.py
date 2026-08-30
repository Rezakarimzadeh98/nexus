from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from nexus_core.evaluation.metrics import (
    brier_score,
    detection_lead_hours,
    false_positive_rate,
    precision_recall_f1,
)
from nexus_core.evaluation.replay import blind_forecast_protocol, filter_before


def test_brier_and_clf_metrics() -> None:
    assert brier_score([0.0, 1.0], [0, 1]) == 0.0
    assert brier_score([1.0], [0]) == 1.0
    scores = precision_recall_f1([1, 0, 1, 0], [1, 1, 0, 0])
    assert scores["tp"] == 1
    assert scores["fp"] == 1
    assert scores["fn"] == 1
    assert scores["tn"] == 1
    assert false_positive_rate(1, 1) == 0.5


def test_blind_forecast_protocol() -> None:
    now = datetime.now(tz=UTC)
    cutoff = now - timedelta(hours=72)
    events = []
    for i in range(10):
        events.append(
            (
                uuid4(),
                "NaturalHazard",
                cutoff - timedelta(hours=i * 24),
                [uuid4()],
            )
        )
    # Outcomes after cutoff
    events.append((uuid4(), "NaturalHazard", cutoff + timedelta(hours=12), [uuid4()]))
    events.append((uuid4(), "Mention", cutoff + timedelta(hours=20), [uuid4()]))

    past = filter_before(events, cutoff)
    assert all((e[2] or cutoff) <= cutoff for e in past)

    result = blind_forecast_protocol(events, cutoff=cutoff, horizon_hours=72)
    assert result["n_scored"] >= 1
    assert result["brier_score"] is not None
    assert 0.0 <= float(result["brier_score"]) <= 1.0


def test_detection_lead() -> None:
    now = datetime.now(tz=UTC)
    signals = [now - timedelta(hours=10)]
    changes = [now - timedelta(hours=2)]
    lead = detection_lead_hours(signals, changes, max_lead_hours=72)
    assert lead["matched"] == 1
    assert abs(lead["mean_lead_hours"] - 8.0) < 0.01
