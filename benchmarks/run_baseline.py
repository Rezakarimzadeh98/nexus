#!/usr/bin/env python3
"""Run the public benchmark scorecard and print JSON."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow running from repo root without install in some environments
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nexus_core.config import get_settings  # noqa: E402
from nexus_core.db import make_engine, make_session_factory  # noqa: E402
from nexus_core.evaluation import run_evaluation  # noqa: E402


def main() -> int:
    settings = get_settings()
    engine = make_engine(settings)
    factory = make_session_factory(engine)
    with factory() as session:
        scorecard = run_evaluation(session, horizon_hours=72.0)
    print(json.dumps(scorecard, indent=2))
    out = ROOT / "benchmarks" / "last_scorecard.json"
    out.write_text(json.dumps(scorecard, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
