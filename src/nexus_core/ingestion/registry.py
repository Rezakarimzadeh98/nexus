from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from nexus_core.ingestion.models import SourceConfig, SourceType


def load_sources(path: str | Path) -> list[SourceConfig]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    items = data.get("sources", [])
    sources: list[SourceConfig] = []
    for item in items:
        sources.append(
            SourceConfig(
                id=str(item["id"]),
                type=SourceType(str(item["type"])),
                enabled=bool(item.get("enabled", True)),
                url=item.get("url"),
                path=item.get("path"),
                poll_seconds=int(item.get("poll_seconds", 3600)),
                rate_limit_per_minute=int(item.get("rate_limit_per_minute", 30)),
                metadata=dict(item.get("metadata") or {}),
            )
        )
    return sources


def dump_sources_summary(sources: list[SourceConfig]) -> list[dict[str, Any]]:
    return [
        {
            "id": s.id,
            "type": s.type.value,
            "enabled": s.enabled,
            "url": s.url,
            "path": s.path,
        }
        for s in sources
    ]
