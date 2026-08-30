from __future__ import annotations

from nexus_core.types import Forecast, Scenario


def _normalize(weights: list[float]) -> list[float]:
    total = sum(max(w, 0.0) for w in weights)
    if total <= 0:
        n = len(weights) or 1
        return [1.0 / n] * len(weights)
    return [max(w, 0.0) / total for w in weights]


def build_scenarios(
    forecast: Forecast,
    *,
    velocity: float | None = None,
    pattern_boost: float = 0.0,
) -> list[Scenario]:
    """2–3 scenarios with probabilities summing to ~1.0."""
    base = forecast.probability
    vel = velocity if velocity is not None else 1.0
    elevate = min(0.55, base * (0.55 + 0.15 * max(vel - 1.0, 0.0)) + 0.1 * pattern_boost)
    cool = min(0.55, (1.0 - base) * 0.65)
    status = max(0.15, 1.0 - elevate - cool)
    elevate_n, status_n, cool_n = _normalize([elevate, status, cool])

    return [
        Scenario(
            label="elevated_activity",
            probability=round(elevate_n, 4),
            drivers=[
                f"baseline hazard {base:.2f}",
                f"velocity {vel:.2f}x" if velocity is not None else "velocity unknown",
                *(["pattern prefix match"] if pattern_boost > 0 else []),
            ],
            summary="Activity at or above the recent hazard rate continues into the horizon.",
        ),
        Scenario(
            label="status_quo",
            probability=round(status_n, 4),
            drivers=["historical cadence", "no strong deviation assumed"],
            summary="Rates stay near the lookback average without a sharp spike or lull.",
        ),
        Scenario(
            label="cooling",
            probability=round(cool_n, 4),
            drivers=["mean reversion", "quiet stretch possible"],
            summary="Fewer events than the hazard baseline suggests for this horizon.",
        ),
    ]
