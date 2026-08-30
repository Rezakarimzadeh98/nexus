from __future__ import annotations

from datetime import datetime


def brier_score(probabilities: list[float], outcomes: list[int]) -> float:
    """Mean squared error between predicted probs and binary outcomes (0/1)."""
    if not probabilities or len(probabilities) != len(outcomes):
        return 0.0
    total = 0.0
    for p, y in zip(probabilities, outcomes, strict=True):
        p_clamped = min(max(p, 0.0), 1.0)
        y_i = 1.0 if y else 0.0
        total += (p_clamped - y_i) ** 2
    return round(total / len(probabilities), 6)


def precision_recall_f1(
    y_true: list[int],
    y_pred: list[int],
) -> dict[str, float]:
    tp = fp = fn = tn = 0
    for yt, yp in zip(y_true, y_pred, strict=True):
        if yp and yt:
            tp += 1
        elif yp and not yt:
            fp += 1
        elif not yp and yt:
            fn += 1
        else:
            tn += 1
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    )
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": float(tp),
        "fp": float(fp),
        "fn": float(fn),
        "tn": float(tn),
    }


def false_positive_rate(fp: int, tn: int) -> float:
    denom = fp + tn
    if denom <= 0:
        return 0.0
    return round(fp / denom, 4)


def detection_lead_hours(
    signal_times: list[datetime],
    change_times: list[datetime],
    *,
    max_lead_hours: float = 72.0,
) -> dict[str, float]:
    """Average lead time of signals that precede a labeled change within max_lead."""
    if not signal_times or not change_times:
        return {
            "mean_lead_hours": 0.0,
            "matched": 0.0,
            "missed_changes": float(len(change_times)),
        }

    leads: list[float] = []
    matched_changes = 0
    for change in sorted(change_times):
        best: float | None = None
        for sig in signal_times:
            delta_h = (change - sig).total_seconds() / 3600.0
            if 0 <= delta_h <= max_lead_hours:
                if best is None or delta_h < best:
                    best = delta_h
        if best is not None:
            leads.append(best)
            matched_changes += 1
    mean_lead = sum(leads) / len(leads) if leads else 0.0
    return {
        "mean_lead_hours": round(mean_lead, 4),
        "matched": float(matched_changes),
        "missed_changes": float(len(change_times) - matched_changes),
    }
