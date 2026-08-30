from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_CALIBRATION_PATH = Path("models/calibration.json")


def fit_calibration(scored: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Fit a simple affine calibration: p' = clip(a * p + b).
    Uses mean predicted vs mean outcome (temperature-style scale).
    """
    if not scored:
        return {
            "a": 1.0,
            "b": 0.0,
            "n": 0,
            "method": "identity",
            "mean_predicted": 0.0,
            "mean_outcome": 0.0,
        }

    preds = [float(r.get("probability") or 0.0) for r in scored]
    outcomes = [float(int(r.get("outcome") or 0)) for r in scored]
    mean_p = sum(preds) / len(preds)
    mean_y = sum(outcomes) / len(outcomes)

    # Scale so mean prediction moves toward mean outcome; keep intercept small.
    if mean_p < 1e-6:
        a, b = 1.0, mean_y
        method = "intercept_only"
    else:
        a = mean_y / mean_p
        # Bound aggressive rescaling
        a = max(0.25, min(a, 2.5))
        b = 0.0
        method = "mean_ratio"

    return {
        "a": round(a, 6),
        "b": round(b, 6),
        "n": len(scored),
        "method": method,
        "mean_predicted": round(mean_p, 6),
        "mean_outcome": round(mean_y, 6),
    }


def apply_calibration(probability: float, calibration: dict[str, Any]) -> float:
    a = float(calibration.get("a", 1.0))
    b = float(calibration.get("b", 0.0))
    p = a * probability + b
    return max(0.0, min(p, 0.95))


def save_calibration(calibration: dict[str, Any], path: Path | None = None) -> Path:
    target = path or DEFAULT_CALIBRATION_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "model_id": "hazard_rate_v1",
        "calibration": calibration,
    }
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return target


def load_calibration(path: Path | None = None) -> dict[str, Any]:
    target = path or DEFAULT_CALIBRATION_PATH
    if not target.is_file():
        return {"a": 1.0, "b": 0.0, "n": 0, "method": "identity"}
    data = json.loads(target.read_text(encoding="utf-8"))
    cal = data.get("calibration") if isinstance(data, dict) else None
    if isinstance(cal, dict):
        return cal
    return {"a": 1.0, "b": 0.0, "n": 0, "method": "identity"}
