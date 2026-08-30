from __future__ import annotations

import argparse
from pathlib import Path

from sqlalchemy import func, select

from nexus_core import __version__
from nexus_core.config import get_settings
from nexus_core.db import make_engine, make_session_factory
from nexus_core.db.models import (
    EntityRow,
    EventRow,
    ForecastRow,
    ObservationRow,
    PatternRow,
    RelationRow,
    SignalRow,
)
from nexus_core.detection import (
    build_live_snapshot,
    compute_state_snapshots,
    detect_signals,
    persist_signals,
    persist_states,
    write_live_snapshot,
)
from nexus_core.detection.export import observations_from_rows
from nexus_core.discovery import run_discovery
from nexus_core.extraction import extract_entities, extract_events, extract_relations
from nexus_core.extraction.store import persist_entities, persist_events, persist_relations
from nexus_core.forecast import run_forecast
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

    detect_p = sub.add_parser("detect", help="Compute state snapshots and What-Changed signals")
    detect_p.add_argument("--limit", type=int, default=2000)
    detect_p.add_argument("--velocity-threshold", type=float, default=1.5)
    detect_p.add_argument("--min-short-volume", type=float, default=2.0)

    export_p = sub.add_parser("export-live", help="Write public live snapshot JSON")
    export_p.add_argument("--out", default="docs/live/status.json")

    discover_p = sub.add_parser(
        "discover",
        help="Mine patterns and build scoped graph neighborhood",
    )
    discover_p.add_argument("--min-count", type=int, default=2)

    forecast_p = sub.add_parser("forecast", help="Baseline hazard-rate forecasts + scenarios")
    forecast_p.add_argument("--horizon-hours", type=float, default=72.0)

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
                ("patterns", PatternRow),
                ("forecasts", ForecastRow),
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

    if args.command == "detect":
        engine = make_engine(settings)
        factory = make_session_factory(engine)
        with factory() as session:
            obs_rows = list(
                session.execute(
                    select(ObservationRow)
                    .order_by(ObservationRow.fetched_at.desc())
                    .limit(args.limit)
                )
                .scalars()
                .all()
            )
            observations = observations_from_rows(obs_rows)
            snapshots = compute_state_snapshots(observations)
            signals = detect_signals(
                snapshots,
                observations,
                velocity_threshold=args.velocity_threshold,
                min_short_volume=args.min_short_volume,
            )
            sn = persist_states(session, snapshots)
            sg = persist_signals(session, signals)
            session.commit()
        print(
            f"version={__version__}\tobservations={len(observations)}\t"
            f"states={sn}\tsignals={sg}"
        )
        return 0

    if args.command == "export-live":
        engine = make_engine(settings)
        factory = make_session_factory(engine)
        out = Path(args.out)
        with factory() as session:
            # Prefer freshly computed in-memory if we re-run detect first;
            # export uses whatever is already persisted.
            payload = build_live_snapshot(session)
            write_live_snapshot(out, payload)
        print(f"wrote\t{out}\tsignals={len(payload.get('signals', []))}")
        return 0

    if args.command == "discover":
        engine = make_engine(settings)
        factory = make_session_factory(engine)
        with factory() as session:
            discovery = run_discovery(session, min_count=args.min_count, persist=True)
            session.commit()
        counts = discovery.get("counts", {})
        print(
            f"version={__version__}\tpatterns={counts.get('patterns', 0)}\t"
            f"matches={counts.get('pattern_matches', 0)}\t"
            f"graph_nodes={counts.get('graph_nodes', 0)}\t"
            f"graph_edges={counts.get('graph_edges', 0)}"
        )
        return 0

    if args.command == "forecast":
        engine = make_engine(settings)
        factory = make_session_factory(engine)
        with factory() as session:
            discovery = run_discovery(session, persist=False)
            matched = {
                (m.get("expected_next") or "")
                for m in discovery.get("pattern_matches", [])
                if isinstance(m, dict)
            }
            result_fc = run_forecast(
                session,
                horizon_hours=args.horizon_hours,
                persist=True,
                pattern_match_types={t for t in matched if t},
            )
            session.commit()
        print(
            f"version={__version__}\t"
            f"forecasts={result_fc.get('counts', {}).get('forecasts', 0)}\t"
            f"horizon_hours={args.horizon_hours}"
        )
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
