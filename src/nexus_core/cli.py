from __future__ import annotations

import argparse
from pathlib import Path

from sqlalchemy import func, select

from nexus_core import __version__
from nexus_core.config import get_settings
from nexus_core.db import make_engine, make_session_factory
from nexus_core.db.models import EntityRow, EventRow, ObservationRow, RelationRow, SignalRow
from nexus_core.extraction import extract_entities, extract_events, extract_relations
from nexus_core.extraction.store import persist_entities, persist_events, persist_relations
from nexus_core.ingestion import ingest_many
from nexus_core.ingestion.registry import dump_sources_summary, load_sources
from nexus_core.logging import configure_logging, get_logger
from nexus_core.types import Observation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="nexus", description="NEXUS CLI")
    parser.add_argument("--version", action="store_true", help="Print version")
    sub = parser.add_subparsers(dest="command")

    ingest_p = sub.add_parser("ingest", help="Ingest configured sources (official by default)")
    ingest_p.add_argument("--sources", default="adapters/generic/sources.yaml")
    ingest_p.add_argument("--fixture-root", default="datasets")
    ingest_p.add_argument("--dry-run", action="store_true")
    ingest_p.add_argument("--source-id", default=None)

    list_p = sub.add_parser("sources", help="List configured sources")
    list_p.add_argument("--sources", default="adapters/generic/sources.yaml")

    extract_p = sub.add_parser(
        "extract",
        help="Extract entities/events/relations from DB observations",
    )
    extract_p.add_argument("--limit", type=int, default=500)

    sub.add_parser("status", help="Show version and database counters")

    args = parser.parse_args(argv)
    settings = get_settings()
    configure_logging(settings.log_level)
    log = get_logger("nexus.cli")

    if args.version:
        print(f"nexus {__version__}")
        return 0

    if args.command is None:
        print(f"nexus {__version__}")
        parser.print_help()
        return 0

    if args.command == "sources":
        sources = load_sources(args.sources)
        for row in dump_sources_summary(sources):
            print(f"{row['id']}\t{row['type']}\tenabled={row['enabled']}")
        return 0

    if args.command == "status":
        print(f"version\t{__version__}")
        print(f"environment\t{settings.environment}")
        engine = make_engine(settings)
        factory = make_session_factory(engine)
        with factory() as session:
            for label, model in (
                ("observations", ObservationRow),
                ("entities", EntityRow),
                ("events", EventRow),
                ("relations", RelationRow),
                ("signals", SignalRow),
            ):
                count = session.execute(select(func.count()).select_from(model)).scalar_one()
                print(f"{label}\t{count}")
        return 0

    if args.command == "ingest":
        sources = load_sources(args.sources)
        if args.source_id:
            sources = [s for s in sources if s.id == args.source_id]
        fixture_root = Path(args.fixture_root)
        if args.dry_run:
            results = ingest_many(None, sources, fixture_root=fixture_root, persist=False)
        else:
            engine = make_engine(settings)
            factory = make_session_factory(engine)
            with factory() as session:
                results = ingest_many(session, sources, fixture_root=fixture_root, persist=True)
                session.commit()
        failures = 0
        for result in results:
            if result.error == "disabled":
                print(f"{result.source_id}\tdisabled")
                continue
            status = "ok" if result.error is None else f"error={result.error}"
            print(
                f"{result.source_id}\tfetched={result.fetched}\t"
                f"observations={result.observation_count}\tinserted={result.inserted}\t{status}"
            )
            if result.error:
                failures += 1
                log.error("source failed: %s", result.source_id)
        return 1 if failures else 0

    if args.command == "extract":
        engine = make_engine(settings)
        factory = make_session_factory(engine)
        with factory() as session:
            rows = session.execute(
                select(ObservationRow).order_by(ObservationRow.fetched_at.desc()).limit(args.limit)
            ).scalars()
            observations = [
                Observation(
                    id=row.id,
                    source_id=row.source_id,
                    title=row.title,
                    body=row.body,
                    url=row.url,
                    published_at=row.published_at,
                    fetched_at=row.fetched_at,
                    language=row.language,
                    raw_hash=row.raw_hash,
                    raw_uri=row.raw_uri,
                    metadata=row.metadata_json or {},
                )
                for row in rows
            ]
            entities = extract_entities(observations)
            events = extract_events(observations, entities)
            relations = extract_relations(observations, entities)
            e_n = persist_entities(session, entities)
            ev_n = persist_events(session, events)
            r_n = persist_relations(session, relations)
            session.commit()
        print(
            f"version={__version__}\tobservations={len(observations)}\t"
            f"entities_new={e_n}\tevents_new={ev_n}\trelations_new={r_n}"
        )
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
