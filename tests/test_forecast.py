from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from nexus_core.forecast.engine import build_forecasts, hazard_probability
from nexus_core.forecast.scenarios import build_scenarios
from nexus_core.types import Forecast, ForecastQuestion


def test_hazard_probability_bounds() -> None:
    assert hazard_probability(rate_per_hour=0.0, horizon_hours=72) == 0.0
    p = hazard_probability(rate_per_hour=0.1, horizon_hours=24)
    assert 0.0 < p <= 0.95


def test_build_forecasts_and_scenarios() -> None:
    now = datetime.now(tz=UTC)
    events = []
    for i in range(12):
        events.append(
            (
                uuid4(),
                "NaturalHazard",
                now - timedelta(hours=i * 20),
                [uuid4()],
            )
        )
    forecasts = build_forecasts(events, horizon_hours=72, top_k=3)
    assert forecasts
    f = forecasts[0]
    assert f.question.event_type == "NaturalHazard"
    assert 0.0 <= f.probability <= 0.95
    assert f.evidence_event_ids
    assert "sure claim" in (f.summary or "").lower() or "probability" in (f.summary or "").lower()

    scenarios = build_scenarios(f, velocity=2.0, pattern_boost=1.0)
    assert len(scenarios) == 3
    total = sum(s.probability for s in scenarios)
    assert abs(total - 1.0) < 0.02


def test_forecast_question_schema() -> None:
    q = ForecastQuestion(event_type="Vulnerability", horizon_hours=48)
    f = Forecast(question=q, probability=0.4, confidence=0.55, horizon_hours=48)
    data = f.model_dump(mode="json")
    assert data["question"]["kind"] == "event_in_horizon"
    assert data["model_id"] == "hazard_rate_v1"
