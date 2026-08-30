from __future__ import annotations

from sqlalchemy.orm import Session

from nexus_core.db.models import SignalRow, StateSnapshotRow
from nexus_core.types import Signal, StateSnapshot


def persist_states(session: Session, snapshots: list[StateSnapshot]) -> int:
    for snap in snapshots:
        session.add(
            StateSnapshotRow(
                id=snap.id,
                scope_key=snap.scope_key,
                captured_at=snap.captured_at,
                metrics=snap.metrics,
                metadata_json=snap.metadata,
            )
        )
    return len(snapshots)


def persist_signals(session: Session, signals: list[Signal]) -> int:
    for signal in signals:
        session.add(
            SignalRow(
                id=signal.id,
                scope_key=signal.scope_key,
                title=signal.title,
                summary=signal.summary,
                severity=signal.severity.value,
                confidence=signal.confidence,
                change_ratio=signal.change_ratio,
                detected_at=signal.detected_at,
                evidence=[e.model_dump(mode="json") for e in signal.evidence],
                contradictions=[c.model_dump(mode="json") for c in signal.contradictions],
                metadata_json=signal.metadata,
            )
        )
    return len(signals)
