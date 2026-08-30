from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from nexus_core.ids import new_id, utc_now


class NexusModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class EntityKind(StrEnum):
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    PRODUCT = "product"
    TECHNOLOGY = "technology"
    ASSET = "asset"
    EVENT = "event"
    OTHER = "other"


class SignalSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Observation(NexusModel):
    """Normalized fact from a source."""

    id: UUID = Field(default_factory=new_id)
    source_id: str
    title: str | None = None
    body: str | None = None
    url: str | None = None
    published_at: datetime | None = None
    fetched_at: datetime = Field(default_factory=utc_now)
    language: str | None = None
    raw_hash: str | None = None
    raw_uri: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Entity(NexusModel):
    id: UUID = Field(default_factory=new_id)
    kind: EntityKind
    name: str
    canonical_key: str
    aliases: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EventRecord(NexusModel):
    """Named `EventRecord` to avoid clashing with threading.Event semantics later."""

    id: UUID = Field(default_factory=new_id)
    type: str
    title: str
    occurred_at: datetime | None = None
    observation_ids: list[UUID] = Field(default_factory=list)
    entity_ids: list[UUID] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Relation(NexusModel):
    id: UUID = Field(default_factory=new_id)
    subject_id: UUID
    predicate: str
    object_id: UUID
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence_observation_ids: list[UUID] = Field(default_factory=list)


class StateSnapshot(NexusModel):
    id: UUID = Field(default_factory=new_id)
    scope_key: str
    captured_at: datetime = Field(default_factory=utc_now)
    metrics: dict[str, float] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceRef(NexusModel):
    observation_id: UUID
    note: str | None = None
    weight: float = Field(default=1.0, ge=0.0)


class Signal(NexusModel):
    id: UUID = Field(default_factory=new_id)
    scope_key: str
    title: str
    summary: str | None = None
    severity: SignalSeverity = SignalSeverity.MEDIUM
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    change_ratio: float | None = None
    detected_at: datetime = Field(default_factory=utc_now)
    evidence: list[EvidenceRef] = Field(default_factory=list)
    contradictions: list[EvidenceRef] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ForecastQuestion(NexusModel):
    """Explicit forecast question — never implied certainty."""

    id: UUID = Field(default_factory=new_id)
    kind: str = "event_in_horizon"
    event_type: str
    horizon_hours: float = Field(default=72.0, gt=0.0)
    scope_key: str = "global"
    text: str | None = None


class Scenario(NexusModel):
    id: UUID = Field(default_factory=new_id)
    label: str
    probability: float = Field(ge=0.0, le=1.0)
    drivers: list[str] = Field(default_factory=list)
    summary: str | None = None


class Forecast(NexusModel):
    id: UUID = Field(default_factory=new_id)
    question: ForecastQuestion
    probability: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    horizon_hours: float
    model_id: str = "hazard_rate_v1"
    created_at: datetime = Field(default_factory=utc_now)
    evidence_event_ids: list[UUID] = Field(default_factory=list)
    evidence_observation_ids: list[UUID] = Field(default_factory=list)
    scenarios: list[Scenario] = Field(default_factory=list)
    summary: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
