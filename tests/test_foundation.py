from __future__ import annotations

from datetime import UTC, datetime

from nexus_core.ids import ensure_utc, new_id, utc_now
from nexus_core.types import Entity, EntityKind, Observation, Signal, SignalSeverity


def test_utc_now_is_aware() -> None:
    now = utc_now()
    assert now.tzinfo is not None
    assert now.utcoffset() is not None
    assert now.utcoffset().total_seconds() == 0


def test_ensure_utc_naive() -> None:
    naive = datetime(2026, 8, 30, 12, 0, 0)
    aware = ensure_utc(naive)
    assert aware.tzinfo == UTC


def test_observation_roundtrip() -> None:
    obs = Observation(source_id="fixture-rss", title="Hello NEXUS", body="foundation")
    data = obs.model_dump(mode="json")
    again = Observation.model_validate(data)
    assert again.source_id == "fixture-rss"
    assert again.id == obs.id


def test_entity_and_signal_defaults() -> None:
    entity = Entity(kind=EntityKind.ORGANIZATION, name="Acme", canonical_key="org:acme")
    signal = Signal(
        scope_key="entity:org:acme",
        title="Activity spike",
        severity=SignalSeverity.HIGH,
        confidence=0.84,
        change_ratio=1.43,
    )
    assert entity.id != new_id()
    assert signal.evidence == []
    assert 0.0 <= signal.confidence <= 1.0


def test_json_schema_exportable() -> None:
    schema = Observation.model_json_schema()
    assert schema["title"] == "Observation"
    assert "source_id" in schema["properties"]
