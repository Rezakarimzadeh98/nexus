from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class SourceType(StrEnum):
    RSS = "rss"
    HTTP_JSON = "http_json"
    CSV = "csv"
    FIXTURE = "fixture"
    USGS_GEOJSON = "usgs_geojson"
    EONET = "eonet"
    ATOM = "atom"
    NVD_CVE = "nvd_cve"
    CISA_KEV = "cisa_kev"


@dataclass(frozen=True)
class SourceConfig:
    id: str
    type: SourceType
    enabled: bool = True
    url: str | None = None
    path: str | None = None
    poll_seconds: int = 3600
    rate_limit_per_minute: int = 30
    metadata: dict[str, Any] = field(default_factory=dict)
