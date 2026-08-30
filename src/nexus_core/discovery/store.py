from __future__ import annotations

from sqlalchemy.orm import Session

from nexus_core.db.models import PatternRow
from nexus_core.discovery.patterns import SequencePattern


def persist_patterns(session: Session, patterns: list[SequencePattern]) -> int:
    inserted = 0
    for pattern in patterns:
        session.add(
            PatternRow(
                id=pattern.id,
                sequence=pattern.sequence,
                support=pattern.support,
                confidence=pattern.confidence,
                count=pattern.count,
                example_event_ids=pattern.example_event_ids,
                metadata_json=pattern.metadata,
            )
        )
        inserted += 1
    return inserted
