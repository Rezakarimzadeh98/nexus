"""Export versioned JSON Schema documents for core interchange types."""

from __future__ import annotations

import json
from pathlib import Path

from nexus_core.discovery.patterns import PatternMatch, SequencePattern
from nexus_core.learning.store import OutcomeRecord
from nexus_core.types import (
    Entity,
    EventRecord,
    EvidenceRef,
    Forecast,
    ForecastQuestion,
    Observation,
    Relation,
    Scenario,
    Signal,
    StateSnapshot,
)

OUT = Path(__file__).resolve().parents[1] / "docs" / "schemas" / "v1"
MODELS = {
    "observation": Observation,
    "entity": Entity,
    "event": EventRecord,
    "relation": Relation,
    "state_snapshot": StateSnapshot,
    "signal": Signal,
    "evidence_ref": EvidenceRef,
    "forecast_question": ForecastQuestion,
    "scenario": Scenario,
    "forecast": Forecast,
    "sequence_pattern": SequencePattern,
    "pattern_match": PatternMatch,
    "outcome_record": OutcomeRecord,
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, model in MODELS.items():
        path = OUT / f"{name}.schema.json"
        path.write_text(json.dumps(model.model_json_schema(), indent=2) + "\n", encoding="utf-8")
        print(f"wrote {path.relative_to(Path.cwd()) if Path.cwd() in path.parents else path}")


if __name__ == "__main__":
    main()
