from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field
from sqlalchemy.orm import Session

from nexus_core.db.models import OutcomeRow
from nexus_core.ids import new_id, utc_now
from nexus_core.types import NexusModel


class OutcomeRecord(NexusModel):
    id: UUID = Field(default_factory=new_id)
    forecast_id: UUID | None = None
    event_type: str
    probability: float
    outcome: int
    horizon_hours: float
    model_id: str = "hazard_rate_v1"
    recorded_at: datetime = Field(default_factory=utc_now)
    cutoff: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


def persist_outcomes(session: Session, outcomes: list[OutcomeRecord]) -> int:
    inserted = 0
    for item in outcomes:
        session.add(
            OutcomeRow(
                id=item.id,
                forecast_id=item.forecast_id,
                event_type=item.event_type,
                probability=item.probability,
                outcome=item.outcome,
                horizon_hours=item.horizon_hours,
                model_id=item.model_id,
                recorded_at=item.recorded_at,
                cutoff=item.cutoff,
                metadata_json=item.metadata,
            )
        )
        inserted += 1
    return inserted
