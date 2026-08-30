from __future__ import annotations

import argparse
from pathlib import Path

from nexus_core import __version__
from nexus_core.config import get_settings
from nexus_core.db import make_engine, make_session_factory
from nexus_core.ingestion import ingest_many
from nexus_core.ingestion.registry import dump_sources_summary, load_sources
from nexus_core.logging import configure_logging, get_logger


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="nexus", description="NEXUS CLI")
    parser.add_argument("--version", action="store_true")
    sub = parser.add_subparsers(dest="command")

    ingest_p = sub.add_parser("ingest", help="Run ingestion for configured sources")
    ingest_p.add_argument(
        "--sources",
        default="adapters/generic/sources.yaml",
        help="Path to sources.yaml",
    )
    ingest_p.add_argument(
        "--fixture-root",
        default="datasets",
        help="Root for relative fixture/csv paths",
    )
    ingest_p.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch/parse without writing to Postgres",
    )
    ingest_p.add_argument("--source-id", default=None, help="Only run one source id")

    list_p = sub.add_parser("sources", help="List configured sources")
    list_p.add_argument("--sources", default="adapters/generic/sources.yaml")

    args = parser.parse_args(argv)
    settings = get_settings()
    configure_logging(settings.log_level)
    log = get_logger("nexus.cli")

    if args.version or args.command is None:
        print(f"nexus {__version__}")
        if args.command is None and not args.version:
            parser.print_help()
        return 0

    if args.command == "sources":
        sources = load_sources(args.sources)
        for row in dump_sources_summary(sources):
            print(f"{row['id']}\t{row['type']}\tenabled={row['enabled']}")
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

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
