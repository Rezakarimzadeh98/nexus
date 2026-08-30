from __future__ import annotations

import csv
import hashlib
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from nexus_core.ids import utc_now
from nexus_core.ingestion.models import SourceConfig, SourceType
from nexus_core.types import Observation

USER_AGENT = "NEXUS-Ingest/0.1 (+https://github.com/Rezakarimzadeh98/nexus)"


@dataclass
class RawFetch:
    source_id: str
    payload: bytes
    content_type: str
    origin: str


def content_hash(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def item_fingerprint(
    source_id: str,
    title: str | None,
    url: str | None,
    body: str | None,
) -> str:
    material = f"{source_id}\n{title or ''}\n{url or ''}\n{body or ''}".encode()
    return hashlib.sha256(material).hexdigest()


def fetch_raw(source: SourceConfig, *, fixture_root: Path | None = None) -> RawFetch:
    if source.type in {SourceType.FIXTURE, SourceType.CSV}:
        if not source.path:
            raise ValueError(f"{source.type.value} source {source.id} requires path")
        path = Path(source.path)
        if fixture_root is not None and not path.is_absolute():
            path = fixture_root / path
        payload = path.read_bytes()
        ctype = "application/json" if source.type == SourceType.FIXTURE else "text/csv"
        return RawFetch(source.id, payload, ctype, str(path))

    if source.url is None:
        raise ValueError(f"source {source.id} requires url")

    req = Request(source.url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=30) as resp:  # noqa: S310 - curated public URLs only
        payload = resp.read()
        content_type = resp.headers.get_content_type() or "application/octet-stream"
    return RawFetch(source.id, payload, content_type, source.url)


def observations_from_raw(source: SourceConfig, raw: RawFetch) -> list[Observation]:
    fetch_digest = content_hash(raw.payload)
    fetched = utc_now()

    if source.type == SourceType.FIXTURE:
        data = json.loads(raw.payload.decode("utf-8"))
        items = data if isinstance(data, list) else data.get("items", [])
        return [
            _obs_from_dict(source.id, item, fetch_digest, fetched, raw.origin) for item in items
        ]

    if source.type == SourceType.CSV:
        text = raw.payload.decode("utf-8")
        reader = csv.DictReader(text.splitlines())
        return [
            _obs_from_dict(source.id, dict(row), fetch_digest, fetched, raw.origin)
            for row in reader
        ]

    if source.type == SourceType.HTTP_JSON:
        data = json.loads(raw.payload.decode("utf-8"))
        items = data if isinstance(data, list) else data.get("items", data.get("articles", []))
        if isinstance(items, dict):
            items = [items]
        return [
            _obs_from_dict(source.id, item, fetch_digest, fetched, raw.origin) for item in items
        ]

    if source.type == SourceType.RSS:
        return _parse_rss(source.id, raw.payload, fetch_digest, fetched, raw.origin)

    raise ValueError(f"unsupported source type: {source.type}")


def _obs_from_dict(
    source_id: str,
    item: dict[str, Any],
    fetch_digest: str,
    fetched: Any,
    origin: str,
) -> Observation:
    title = item.get("title") or item.get("headline") or item.get("name")
    body = item.get("body") or item.get("summary") or item.get("description") or item.get("content")
    url = item.get("url") or item.get("link")
    title_s = str(title) if title is not None else None
    body_s = str(body) if body is not None else None
    url_s = str(url) if url is not None else None
    return Observation(
        source_id=source_id,
        title=title_s,
        body=body_s,
        url=url_s,
        fetched_at=fetched,
        raw_hash=item_fingerprint(source_id, title_s, url_s, body_s),
        raw_uri=origin,
        metadata={"fetch_hash": fetch_digest, "keys": sorted(item.keys())},
    )


def _parse_rss(
    source_id: str,
    payload: bytes,
    fetch_digest: str,
    fetched: Any,
    origin: str,
) -> list[Observation]:
    root = ET.fromstring(payload)
    channel = root.find("channel")
    items = channel.findall("item") if channel is not None else []
    if not items:
        items = root.findall(".//item")
    if not items:
        items = root.findall("{http://www.w3.org/2005/Atom}entry")

    observations: list[Observation] = []
    for item in items:
        title = _child_text(item, "title")
        body = _child_text(item, "description") or _child_text(item, "summary")
        link = _child_text(item, "link")
        observations.append(
            Observation(
                source_id=source_id,
                title=title,
                body=body,
                url=link,
                fetched_at=fetched,
                raw_hash=item_fingerprint(source_id, title, link, body),
                raw_uri=origin,
                metadata={"fetch_hash": fetch_digest},
            )
        )
    return observations


def _child_text(node: ET.Element, name: str) -> str | None:
    child = node.find(name)
    if child is not None and child.text:
        return child.text.strip()
    if name == "link":
        link = node.find("{http://www.w3.org/2005/Atom}link")
        if link is not None and link.attrib.get("href"):
            return link.attrib["href"]
    atom = node.find(f"{{http://www.w3.org/2005/Atom}}{name}")
    if atom is not None and atom.text:
        return atom.text.strip()
    return None
