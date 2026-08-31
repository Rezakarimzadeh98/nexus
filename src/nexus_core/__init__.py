"""NEXUS core package — contracts, config, persistence helpers."""

from nexus_core.types import (
    Entity,
    EntityKind,
    EventRecord,
    EvidenceRef,
    Forecast,
    ForecastQuestion,
    Observation,
    Relation,
    Scenario,
    Signal,
    SignalSeverity,
    StateSnapshot,
)

__version__ = "1.0.0"

__all__ = [
    "__version__",
    "Entity",
    "EntityKind",
    "EventRecord",
    "EvidenceRef",
    "Forecast",
    "ForecastQuestion",
    "Observation",
    "Relation",
    "Scenario",
    "Signal",
    "SignalSeverity",
    "StateSnapshot",
]
