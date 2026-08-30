from __future__ import annotations

from typing import Any


def build_error_report(
    scored: list[dict[str, Any]],
) -> dict[str, Any]:
    """Summarize prediction vs outcome errors for feedback."""
    overconfident: list[dict[str, Any]] = []
    underconfident: list[dict[str, Any]] = []
    by_type: dict[str, list[float]] = {}

    for row in scored:
        p = float(row.get("probability") or 0.0)
        y = int(row.get("outcome") or 0)
        et = str(row.get("event_type") or "unknown")
        err = (p - y) ** 2
        by_type.setdefault(et, []).append(err)

        if p >= 0.7 and y == 0:
            overconfident.append({**row, "error": round(err, 4)})
        if p <= 0.3 and y == 1:
            underconfident.append({**row, "error": round(err, 4)})

    type_brier = {
        k: round(sum(v) / len(v), 6) if v else 0.0 for k, v in sorted(by_type.items())
    }
    return {
        "n": len(scored),
        "overconfident": overconfident[:20],
        "underconfident": underconfident[:20],
        "overconfident_count": len(overconfident),
        "underconfident_count": len(underconfident),
        "brier_by_event_type": type_brier,
        "suggestions": _suggestions(overconfident, underconfident, type_brier),
    }


def _suggestions(
    over: list[dict[str, Any]],
    under: list[dict[str, Any]],
    type_brier: dict[str, float],
) -> list[str]:
    tips: list[str] = []
    if len(over) > len(under) and over:
        tips.append("Model is overconfident on some types — lower hazard rates or raise horizon.")
    if len(under) > len(over) and under:
        tips.append("Model under-calls rare hits — shorten lookback or boost pattern matches.")
    if type_brier:
        worst = max(type_brier.keys(), key=lambda k: type_brier[k])
        tips.append(f"Highest Brier event type: {worst} ({type_brier[worst]:.3f}).")
    if not tips:
        tips.append("No strong systematic bias detected in this window.")
    return tips
