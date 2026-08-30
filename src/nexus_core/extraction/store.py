from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_core.db.models import EntityRow, EventRow, RelationRow
from nexus_core.types import Entity, EventRecord, Relation


def persist_entities(session: Session, entities: list[Entity]) -> int:
    inserted = 0
    for entity in entities:
        existing = session.execute(
            select(EntityRow.id).where(EntityRow.canonical_key == entity.canonical_key).limit(1)
        ).first()
        if existing:
            continue
        session.add(
            EntityRow(
                id=entity.id,
                kind=entity.kind.value,
                name=entity.name,
                canonical_key=entity.canonical_key,
                aliases=entity.aliases,
                metadata_json=entity.metadata,
            )
        )
        inserted += 1
    return inserted


def persist_events(session: Session, events: list[EventRecord]) -> int:
    inserted = 0
    for event in events:
        session.add(
            EventRow(
                id=event.id,
                type=event.type,
                title=event.title,
                occurred_at=event.occurred_at,
                observation_ids=event.observation_ids,
                entity_ids=event.entity_ids,
                confidence=event.confidence,
                metadata_json=event.metadata,
            )
        )
        inserted += 1
    return inserted


def persist_relations(session: Session, relations: list[Relation]) -> int:
    inserted = 0
    for rel in relations:
        session.add(
            RelationRow(
                id=rel.id,
                subject_id=rel.subject_id,
                predicate=rel.predicate,
                object_id=rel.object_id,
                confidence=rel.confidence,
                evidence_observation_ids=rel.evidence_observation_ids,
            )
        )
        inserted += 1
    return inserted
