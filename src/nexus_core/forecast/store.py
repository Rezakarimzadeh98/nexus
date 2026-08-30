from __future__ import annotations

from sqlalchemy.orm import Session

from nexus_core.db.models import ForecastRow
from nexus_core.types import Forecast


def persist_forecasts(session: Session, forecasts: list[Forecast]) -> int:
    inserted = 0
    for forecast in forecasts:
        session.add(
            ForecastRow(
                id=forecast.id,
                question=forecast.question.model_dump(mode="json"),
                probability=forecast.probability,
                confidence=forecast.confidence,
                horizon_hours=forecast.horizon_hours,
                model_id=forecast.model_id,
                created_at=forecast.created_at,
                evidence_event_ids=forecast.evidence_event_ids,
                evidence_observation_ids=forecast.evidence_observation_ids,
                scenarios=[s.model_dump(mode="json") for s in forecast.scenarios],
                summary=forecast.summary,
                metadata_json=forecast.metadata,
            )
        )
        inserted += 1
    return inserted
