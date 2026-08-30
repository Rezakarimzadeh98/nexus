from __future__ import annotations

import re
from collections.abc import Iterable

from nexus_core.ids import new_id
from nexus_core.types import Entity, EntityKind, EventRecord, Observation, Relation

_ORG_HINTS = re.compile(r"\b([A-Z][A-Za-z0-9]*(?:[ -][A-Z][A-Za-z0-9]*)+)\b")
_EVENT_HINTS = (
    ("acquisition", "Acquisition"),
    ("agreement", "Agreement"),
    ("earthquake", "NaturalHazard"),
    ("wildfire", "NaturalHazard"),
    ("volcano", "NaturalHazard"),
    ("flood", "NaturalHazard"),
    ("cve-", "Vulnerability"),
    ("vulnerability", "Vulnerability"),
    ("delay", "Delay"),
    ("congestion", "Disruption"),
    ("outbreak", "HealthEvent"),
    ("market", "MarketMove"),
    ("announcement", "Announcement"),
)


def extract_entities(observations: Iterable[Observation]) -> list[Entity]:
    found: dict[str, Entity] = {}
    for obs in observations:
        # Structured publishers from official feeds
        publisher = (obs.metadata or {}).get("publisher")
        if isinstance(publisher, str) and publisher.strip():
            key = f"org:{publisher.lower().replace(' ', '-')}"
            found.setdefault(
                key,
                Entity(
                    id=new_id(),
                    kind=EntityKind.ORGANIZATION,
                    name=publisher,
                    canonical_key=key,
                    aliases=[publisher],
                    metadata={"from": "provenance"},
                ),
            )
        place = (obs.metadata or {}).get("place")
        if isinstance(place, str) and place.strip():
            key = f"loc:{place.lower().replace(' ', '-')[:80]}"
            found.setdefault(
                key,
                Entity(
                    id=new_id(),
                    kind=EntityKind.LOCATION,
                    name=place,
                    canonical_key=key,
                    aliases=[place],
                ),
            )
        text = f"{obs.title or ''} {obs.body or ''}"
        for match in _ORG_HINTS.findall(text):
            name = match.strip()
            if len(name) < 3:
                continue
            key = f"org:{name.lower().replace(' ', '-')}"
            found.setdefault(
                key,
                Entity(
                    id=new_id(),
                    kind=EntityKind.ORGANIZATION,
                    name=name,
                    canonical_key=key,
                    aliases=[name],
                ),
            )
    return list(found.values())


def extract_events(
    observations: Iterable[Observation],
    entities: list[Entity],
) -> list[EventRecord]:
    by_key = {e.canonical_key: e for e in entities}
    events: list[EventRecord] = []
    for obs in observations:
        text = f"{obs.title or ''} {obs.body or ''}".lower()
        event_type = "Mention"
        for needle, label in _EVENT_HINTS:
            if needle in text:
                event_type = label
                break
        linked: list[Entity] = []
        publisher = (obs.metadata or {}).get("publisher")
        if isinstance(publisher, str):
            key = f"org:{publisher.lower().replace(' ', '-')}"
            if key in by_key:
                linked.append(by_key[key])
        place = (obs.metadata or {}).get("place")
        if isinstance(place, str):
            key = f"loc:{place.lower().replace(' ', '-')[:80]}"
            if key in by_key:
                linked.append(by_key[key])
        events.append(
            EventRecord(
                type=event_type,
                title=obs.title or event_type,
                occurred_at=obs.published_at or obs.fetched_at,
                observation_ids=[obs.id],
                entity_ids=[e.id for e in linked[:8]],
                confidence=0.45 if event_type == "Mention" else 0.7,
                metadata={"source_id": obs.source_id},
            )
        )
    return events


def extract_relations(
    observations: Iterable[Observation],
    entities: list[Entity],
) -> list[Relation]:
    """Create co-mention relations between publisher org and location when both exist."""
    by_key = {e.canonical_key: e for e in entities}
    relations: list[Relation] = []
    for obs in observations:
        publisher = (obs.metadata or {}).get("publisher")
        place = (obs.metadata or {}).get("place")
        if not (isinstance(publisher, str) and isinstance(place, str)):
            continue
        org = by_key.get(f"org:{publisher.lower().replace(' ', '-')}")
        loc = by_key.get(f"loc:{place.lower().replace(' ', '-')[:80]}")
        if org is None or loc is None:
            continue
        relations.append(
            Relation(
                subject_id=org.id,
                predicate="reports_on",
                object_id=loc.id,
                confidence=0.6,
                evidence_observation_ids=[obs.id],
            )
        )
    return relations
