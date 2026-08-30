from __future__ import annotations

from nexus_core.types import Signal, SignalSeverity


def severity_from_ratio(change_ratio: float | None) -> SignalSeverity:
    if change_ratio is None:
        return SignalSeverity.LOW
    if change_ratio >= 4.0:
        return SignalSeverity.CRITICAL
    if change_ratio >= 2.5:
        return SignalSeverity.HIGH
    if change_ratio >= 1.5:
        return SignalSeverity.MEDIUM
    return SignalSeverity.LOW


def annotate_anomaly(signal: Signal) -> Signal:
    """Attach a human-readable why template from fired features."""
    metrics = signal.metadata.get("metrics", {})
    volume_short = metrics.get("volume_short")
    baseline_daily = metrics.get("baseline_daily")
    velocity = metrics.get("velocity")
    diversity = metrics.get("source_diversity")

    parts: list[str] = []
    if volume_short is not None and baseline_daily is not None:
        parts.append(
            f"short-window volume {volume_short:.0f} vs baseline ~{baseline_daily:.2f}/day"
        )
    if velocity is not None:
        parts.append(f"velocity {velocity:.2f}x baseline")
    if diversity is not None and signal.scope_key == "global":
        parts.append(f"source diversity {diversity:.0f}")

    why = "; ".join(parts) if parts else "baseline deviation without detailed features"
    signal.metadata = {**signal.metadata, "why": why, "anomaly": True}
    if signal.summary is None:
        signal.summary = why
    signal.severity = severity_from_ratio(signal.change_ratio)
    return signal
