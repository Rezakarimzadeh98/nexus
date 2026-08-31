from __future__ import annotations

from pathlib import Path

from nexus_core.discovery.patterns import SequencePattern
from nexus_core.learning.store import OutcomeRecord
from nexus_core.types import Forecast, ForecastQuestion, Observation, Scenario


def test_export_and_v1_schema_files() -> None:
    from scripts.export_schemas import MODELS, main

    main()
    root = Path("docs/schemas/v1")
    for name in MODELS:
        path = root / f"{name}.schema.json"
        assert path.is_file(), name
        assert path.stat().st_size > 20


def test_core_models_export_json_schema() -> None:
    models = (
        Observation,
        ForecastQuestion,
        Scenario,
        Forecast,
        SequencePattern,
        OutcomeRecord,
    )
    for model in models:
        schema = model.model_json_schema()
        assert isinstance(schema, dict)
        assert schema
