"""Add outcomes table for learning feedback.

Revision ID: 0004_outcomes
Revises: 0003_forecasts
Create Date: 2026-08-30
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_outcomes"
down_revision: str | None = "0003_forecasts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "outcomes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("forecast_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("probability", sa.Float(), nullable=False, server_default="0"),
        sa.Column("outcome", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("horizon_hours", sa.Float(), nullable=False, server_default="72"),
        sa.Column("model_id", sa.String(128), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cutoff", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.create_index("ix_outcomes_forecast_id", "outcomes", ["forecast_id"])
    op.create_index("ix_outcomes_event_type", "outcomes", ["event_type"])
    op.create_index("ix_outcomes_model_id", "outcomes", ["model_id"])
    op.create_index("ix_outcomes_recorded_at", "outcomes", ["recorded_at"])


def downgrade() -> None:
    op.drop_index("ix_outcomes_recorded_at", table_name="outcomes")
    op.drop_index("ix_outcomes_model_id", table_name="outcomes")
    op.drop_index("ix_outcomes_event_type", table_name="outcomes")
    op.drop_index("ix_outcomes_forecast_id", table_name="outcomes")
    op.drop_table("outcomes")
