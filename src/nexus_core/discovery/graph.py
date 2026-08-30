from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from nexus_core.db.models import EntityRow, EventRow, RelationRow


@dataclass
class GraphNode:
    id: str
    kind: str
    label: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "label": self.label,
            "metadata": self.metadata,
        }


@dataclass
class GraphEdge:
    source: str
    target: str
    predicate: str
    confidence: float = 0.5

    def as_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "predicate": self.predicate,
            "confidence": self.confidence,
        }


@dataclass
class GraphNeighborhood:
    center_id: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    depth: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "center_id": self.center_id,
            "depth": self.depth,
            "nodes": [n.as_dict() for n in self.nodes],
            "edges": [e.as_dict() for e in self.edges],
        }


def _entity_node(row: EntityRow) -> GraphNode:
    return GraphNode(
        id=str(row.id),
        kind=row.kind,
        label=row.name,
        metadata={"canonical_key": row.canonical_key},
    )


def build_neighborhood(
    session: Session,
    *,
    entity_id: UUID | None = None,
    canonical_key: str | None = None,
    depth: int = 1,
    limit: int = 48,
) -> GraphNeighborhood | None:
    """Return a scoped 1–2 hop neighborhood around an entity (relations + co-events)."""
    depth = max(1, min(depth, 2))
    limit = max(4, min(limit, 120))

    center: EntityRow | None = None
    if entity_id is not None:
        center = session.get(EntityRow, entity_id)
    elif canonical_key:
        center = session.execute(
            select(EntityRow).where(EntityRow.canonical_key == canonical_key).limit(1)
        ).scalar_one_or_none()
    if center is None:
        # Fallback: most-connected entity by relation degree
        center = _pick_hub(session)
    if center is None:
        return None

    nodes: dict[str, GraphNode] = {str(center.id): _entity_node(center)}
    edges: list[GraphEdge] = []
    frontier: set[UUID] = {center.id}

    for _hop in range(depth):
        if len(nodes) >= limit:
            break
        ids = list(frontier)
        frontier = set()
        if not ids:
            break

        rels = session.execute(
            select(RelationRow).where(
                or_(RelationRow.subject_id.in_(ids), RelationRow.object_id.in_(ids))
            )
        ).scalars().all()

        neighbor_ids: set[UUID] = set()
        for rel in rels:
            edges.append(
                GraphEdge(
                    source=str(rel.subject_id),
                    target=str(rel.object_id),
                    predicate=rel.predicate,
                    confidence=rel.confidence,
                )
            )
            neighbor_ids.add(rel.subject_id)
            neighbor_ids.add(rel.object_id)

        # Co-mention edges from events that share entities with the frontier
        id_set = set(ids)
        events = (
            session.execute(select(EventRow).order_by(EventRow.occurred_at.desc()).limit(400))
            .scalars()
            .all()
        )
        for event in events:
            linked = list(event.entity_ids or [])
            if not any(eid in id_set for eid in linked):
                continue
            for eid in linked:
                neighbor_ids.add(eid)
            for i, a in enumerate(linked):
                for b in linked[i + 1 :]:
                    edges.append(
                        GraphEdge(
                            source=str(a),
                            target=str(b),
                            predicate="co_mentioned",
                            confidence=float(event.confidence),
                        )
                    )

        missing = [eid for eid in neighbor_ids if str(eid) not in nodes]
        if missing:
            rows = (
                session.execute(select(EntityRow).where(EntityRow.id.in_(missing)))
                .scalars()
                .all()
            )
            for row in rows:
                if len(nodes) >= limit:
                    break
                nodes[str(row.id)] = _entity_node(row)
                frontier.add(row.id)

    # Deduplicate edges
    seen: set[tuple[str, str, str]] = set()
    unique_edges: list[GraphEdge] = []
    for edge in edges:
        if edge.source not in nodes or edge.target not in nodes:
            continue
        key = (edge.source, edge.target, edge.predicate)
        if key in seen:
            continue
        seen.add(key)
        unique_edges.append(edge)

    return GraphNeighborhood(
        center_id=str(center.id),
        nodes=list(nodes.values()),
        edges=unique_edges[: limit * 3],
        depth=depth,
    )


def _pick_hub(session: Session) -> EntityRow | None:
    degree: dict[UUID, int] = defaultdict(int)
    for rel in session.execute(select(RelationRow).limit(2000)).scalars():
        degree[rel.subject_id] += 1
        degree[rel.object_id] += 1
    if not degree:
        return session.execute(select(EntityRow).limit(1)).scalar_one_or_none()
    hub_id = max(degree.keys(), key=lambda k: degree[k])
    return session.get(EntityRow, hub_id)


def build_scoped_graph_summary(
    session: Session,
    *,
    max_nodes: int = 36,
) -> dict[str, Any]:
    """Compact graph for the live dashboard (hub neighborhood, not whole world)."""
    nb = build_neighborhood(session, depth=1, limit=max_nodes)
    if nb is None:
        return {"center_id": None, "depth": 0, "nodes": [], "edges": []}
    return nb.as_dict()
