from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from nexus_core.ids import ensure_utc, utc_now
from nexus_core.types import Observation

_WS = re.compile(r"\s+")


@dataclass
class NormalizeStats:
    input_count: int = 0
    dropped_empty: int = 0
    dropped_duplicate: int = 0
    output_count: int = 0


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = _WS.sub(" ", value).strip()
    return cleaned or None


def detect_language_hint(text: str | None) -> str | None:
    """Tiny heuristic placeholder — full language ID lands in a later iteration."""
    if not text:
        return None
    # Latin-heavy demo default
    ascii_ratio = sum(1 for ch in text if ord(ch) < 128) / max(len(text), 1)
    return "en" if ascii_ratio > 0.85 else None


def near_duplicate_key(obs: Observation) -> str:
    title = (obs.title or "").lower()
    source = obs.source_id
    day = ""
    if obs.published_at is not None:
        day = ensure_utc(obs.published_at).date().isoformat()
    elif obs.fetched_at is not None:
        day = ensure_utc(obs.fetched_at).date().isoformat()
    material = f"{source}|{day}|{title}".encode()
    return hashlib.sha256(material).hexdigest()


def normalize_observation(obs: Observation) -> Observation | None:
    title = normalize_text(obs.title)
    body = normalize_text(obs.body)
    if not title and not body:
        return None

    published = ensure_utc(obs.published_at) if obs.published_at else None
    fetched = ensure_utc(obs.fetched_at) if obs.fetched_at else utc_now()
    language = obs.language or detect_language_hint(f"{title or ''} {body or ''}")

    return obs.model_copy(
        update={
            "title": title,
            "body": body,
            "published_at": published,
            "fetched_at": fetched,
            "language": language,
            "url": normalize_text(obs.url),
        }
    )


def normalize_batch(observations: list[Observation]) -> tuple[list[Observation], NormalizeStats]:
    stats = NormalizeStats(input_count=len(observations))
    seen: set[str] = set()
    output: list[Observation] = []
    for obs in observations:
        normalized = normalize_observation(obs)
        if normalized is None:
            stats.dropped_empty += 1
            continue
        key = near_duplicate_key(normalized)
        if key in seen:
            stats.dropped_duplicate += 1
            continue
        seen.add(key)
        output.append(normalized)
    stats.output_count = len(output)
    return output, stats
