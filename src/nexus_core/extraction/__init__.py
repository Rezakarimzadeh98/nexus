from __future__ import annotations

import re
from collections.abc import Iterable

from nexus_core.ids import new_id
from nexus_core.types import Entity, EntityKind, EventRecord, Observation

_ORG_HINTS = re.compile(
    r"\b([A-Z][A-Za-z0-9]*(?:[ -][A-Z][A-Za-z0-9]*)+)\b"
)
_EVENT_HINTS = (
    ("acquisition", "Acquisition"),
    ("agreement", "Agreement"),
    ("delay", "Delay"),
    ("congestion", "Disruption"),
    ("forecast", "Announcement"),
    ("phase", "Announcement"),
    ("market", "MarketMove"),
)


def extract_entities(observations: Iterable[Observation]) -> list[Entity]:
    found: dict[str, Entity] = {}
    for obs in observations:
        text = f"{obs.title or ''} {obs.body or ''}"
        for match in _ORG_HINTS.findall(text):
            name = match.strip()
            if len(name.split()) < 2 and name.lower() in {"the", "and"}:
                continue
            key = f"org:{name.lower().replace(' ', '-')}"
            if key not in found:
                found[key] = Entity(
                    id=new_id(),
                    kind=EntityKind.ORGANIZATION,
                    name=name,
                    canonical_key=key,
                    aliases=[name],
                )
    return list(found.values())


def extract_events(
    observations: Iterable[Observation],
    entities: list[Entity],
) -> list[EventRecord]:
    entity_ids = [e.id for e in entities]
    events: list[EventRecord] = []
    for obs in observations:
        text = f"{obs.title or ''} {obs.body or ''}".lower()
        event_type = "Mention"
        for needle, label in _EVENT_HINTS:
            if needle in text:
                event_type = label
                break
        events.append(
            EventRecord(
                type=event_type,
                title=obs.title or event_type,
                occurred_at=obs.published_at or obs.fetched_at,
                observation_ids=[obs.id],
                entity_ids=entity_ids[:5],
                confidence=0.4 if event_type == "Mention" else 0.6,
            )
        )
    return events
