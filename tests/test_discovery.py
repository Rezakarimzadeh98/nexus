from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from nexus_core.discovery.patterns import match_pattern_prefixes, mine_sequences


def test_mine_and_match_sequences() -> None:
    now = datetime.now(tz=UTC)
    events = []
    # Repeat NaturalHazard -> Vulnerability -> Mention enough times
    for i in range(6):
        base = now - timedelta(hours=30 - i * 3)
        events.extend(
            [
                (uuid4(), "NaturalHazard", base),
                (uuid4(), "Vulnerability", base + timedelta(hours=1)),
                (uuid4(), "Mention", base + timedelta(hours=2)),
            ]
        )
    # Noise
    events.append((uuid4(), "Announcement", now - timedelta(hours=1)))

    patterns = mine_sequences(events, length=3, min_count=2)
    assert patterns
    top = patterns[0]
    assert top.sequence == ["NaturalHazard", "Vulnerability", "Mention"]
    assert top.count >= 2
    assert top.confidence > 0.5

    matches = match_pattern_prefixes(
        patterns,
        ["NaturalHazard", "Vulnerability"],
        min_confidence=0.5,
    )
    assert matches
    assert matches[0].expected_next == "Mention"
    assert "Seen before" in matches[0].title
