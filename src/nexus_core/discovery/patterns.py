from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from nexus_core.ids import new_id, utc_now
from nexus_core.types import NexusModel


class SequencePattern(NexusModel):
    id: UUID = Field(default_factory=new_id)
    sequence: list[str]
    support: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    count: int = 0
    example_event_ids: list[UUID] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PatternMatch(NexusModel):
    id: UUID = Field(default_factory=new_id)
    pattern_id: UUID
    sequence: list[str]
    matched_prefix: list[str]
    expected_next: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    title: str
    summary: str | None = None
    detected_at: datetime = Field(default_factory=utc_now)
    example_event_ids: list[UUID] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


@dataclass
class _EventPoint:
    id: UUID
    type: str
    occurred_at: datetime


def mine_sequences(
    events: list[tuple[UUID, str, datetime | None]],
    *,
    length: int = 3,
    min_count: int = 2,
) -> list[SequencePattern]:
    """Mine frequent event-type sequences A→B→C with support and confidence."""
    length = max(2, min(length, 5))
    points: list[_EventPoint] = []
    for eid, etype, occurred in events:
        if not etype:
            continue
        points.append(
            _EventPoint(id=eid, type=etype, occurred_at=occurred or utc_now())
        )
    points.sort(key=lambda p: p.occurred_at)
    if len(points) < length:
        return []

    total_windows = max(len(points) - length + 1, 1)
    seq_counts: Counter[tuple[str, ...]] = Counter()
    seq_examples: dict[tuple[str, ...], list[UUID]] = defaultdict(list)
    prefix_counts: Counter[tuple[str, ...]] = Counter()

    for i in range(len(points) - length + 1):
        window = points[i : i + length]
        seq = tuple(p.type for p in window)
        seq_counts[seq] += 1
        if len(seq_examples[seq]) < 5:
            seq_examples[seq].extend(p.id for p in window)
        prefix_counts[seq[:-1]] += 1

    patterns: list[SequencePattern] = []
    for seq, count in seq_counts.items():
        if count < min_count:
            continue
        support = count / total_windows
        prefix = seq[:-1]
        conf = count / max(prefix_counts[prefix], 1)
        patterns.append(
            SequencePattern(
                sequence=list(seq),
                support=round(support, 4),
                confidence=round(conf, 4),
                count=count,
                example_event_ids=seq_examples[seq][:length],
                metadata={"length": length},
            )
        )
    patterns.sort(key=lambda p: (p.confidence, p.support, p.count), reverse=True)
    return patterns


def match_pattern_prefixes(
    patterns: list[SequencePattern],
    recent_types: list[str],
    *,
    min_confidence: float = 0.5,
) -> list[PatternMatch]:
    """Alert when the recent event-type prefix matches a mined pattern."""
    if len(recent_types) < 2:
        return []
    prefix = tuple(recent_types[-2:])
    matches: list[PatternMatch] = []
    for pattern in patterns:
        if len(pattern.sequence) < 3:
            continue
        if tuple(pattern.sequence[:2]) != prefix:
            continue
        if pattern.confidence < min_confidence:
            continue
        expected = pattern.sequence[2]
        arrow = " -> ".join(pattern.sequence)
        matches.append(
            PatternMatch(
                pattern_id=pattern.id,
                sequence=pattern.sequence,
                matched_prefix=list(prefix),
                expected_next=expected,
                confidence=pattern.confidence,
                title=f"Seen before: {arrow}",
                summary=(
                    f"Recent types {prefix[0]} -> {prefix[1]} historically continue "
                    f"to {expected} "
                    f"(confidence {pattern.confidence:.2f}, support {pattern.support:.2f})."
                ),
                example_event_ids=pattern.example_event_ids,
                metadata={"support": pattern.support, "count": pattern.count},
            )
        )
    matches.sort(key=lambda m: m.confidence, reverse=True)
    return matches
