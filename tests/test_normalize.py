from __future__ import annotations

from datetime import UTC, datetime

from nexus_core.normalization import normalize_batch, normalize_observation
from nexus_core.types import Observation


def test_normalize_trims_and_drops_empty() -> None:
    keep = Observation(source_id="s", title="  Hello   NEXUS ", body="  x  ")
    drop = Observation(source_id="s", title="   ", body="")
    assert normalize_observation(drop) is None
    out = normalize_observation(keep)
    assert out is not None
    assert out.title == "Hello NEXUS"
    assert out.language == "en"


def test_normalize_batch_dedupes_near_duplicates() -> None:
    t = datetime(2026, 8, 30, 12, 0, tzinfo=UTC)
    a = Observation(source_id="s", title="Same Title", body="a", published_at=t)
    b = Observation(source_id="s", title="Same Title", body="b", published_at=t)
    out, stats = normalize_batch([a, b])
    assert stats.output_count == 1
    assert stats.dropped_duplicate == 1
    assert len(out) == 1
