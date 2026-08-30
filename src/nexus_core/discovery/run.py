from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_core.db.models import EventRow
from nexus_core.discovery.graph import build_scoped_graph_summary
from nexus_core.discovery.patterns import match_pattern_prefixes, mine_sequences
from nexus_core.discovery.store import persist_patterns


def run_discovery(
    session: Session,
    *,
    min_count: int = 2,
    persist: bool = True,
) -> dict[str, Any]:
    """Mine patterns, match recent prefixes, and build a scoped graph summary."""
    event_rows = list(
        session.execute(select(EventRow).order_by(EventRow.occurred_at.asc()).limit(2000)).scalars()
    )
    triples: list[tuple[UUID, str, datetime | None]] = [
        (row.id, row.type, row.occurred_at) for row in event_rows
    ]
    patterns = mine_sequences(triples, length=3, min_count=min_count)
    recent_types = [row.type for row in event_rows[-12:]]
    matches = match_pattern_prefixes(patterns, recent_types, min_confidence=0.45)

    if persist and patterns:
        persist_patterns(session, patterns[:50])

    graph = build_scoped_graph_summary(session, max_nodes=36)
    return {
        "patterns": [p.model_dump(mode="json") for p in patterns[:20]],
        "pattern_matches": [m.model_dump(mode="json") for m in matches[:10]],
        "graph": graph,
        "counts": {
            "patterns": len(patterns),
            "pattern_matches": len(matches),
            "graph_nodes": len(graph.get("nodes", [])),
            "graph_edges": len(graph.get("edges", [])),
        },
    }
