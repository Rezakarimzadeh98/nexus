from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_core.db.models import ObservationRow
from nexus_core.types import Observation


def observation_exists(session: Session, *, source_id: str, raw_hash: str | None) -> bool:
    if not raw_hash:
        return False
    stmt = select(ObservationRow.id).where(
        ObservationRow.source_id == source_id,
        ObservationRow.raw_hash == raw_hash,
    ).limit(1)
    return session.execute(stmt).first() is not None


def persist_observations(session: Session, observations: list[Observation]) -> int:
    """Insert observations, skipping raw_hash duplicates per source. Returns insert count."""
    inserted = 0
    for obs in observations:
        if observation_exists(session, source_id=obs.source_id, raw_hash=obs.raw_hash):
            continue
        row = ObservationRow(
            id=obs.id,
            source_id=obs.source_id,
            title=obs.title,
            body=obs.body,
            url=str(obs.url) if obs.url is not None else None,
            published_at=obs.published_at,
            fetched_at=obs.fetched_at,
            language=obs.language,
            raw_hash=obs.raw_hash,
            raw_uri=obs.raw_uri,
            metadata_json=obs.metadata,
        )
        session.add(row)
        inserted += 1
    return inserted
