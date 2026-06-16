"""add daily_logs table

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-06-15

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY, UUID

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "daily_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        # Кровотеча та БТТ
        sa.Column("bleeding_intensity", sa.Integer(), nullable=True),
        sa.Column("basal_temperature", sa.Numeric(4, 2), nullable=True),
        # Виділення
        sa.Column("discharge_type", sa.String(50), nullable=True),
        # Біль
        sa.Column("pain_intensity", sa.Integer(), nullable=True),
        sa.Column("pain_location", sa.String(50), nullable=True),
        # ШКТ
        sa.Column("gastro_symptoms", ARRAY(sa.String(50)), nullable=True),
        # Апетит
        sa.Column("appetite_state", sa.String(50), nullable=True),
        # Загальне
        sa.Column("stress_level", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_daily_logs_user_id", "daily_logs", ["user_id"])
    op.create_index("ix_daily_logs_date", "daily_logs", ["date"])
    op.create_unique_constraint(
        "uq_daily_logs_user_date", "daily_logs", ["user_id", "date"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_daily_logs_user_date", "daily_logs", type_="unique")
    op.drop_index("ix_daily_logs_date", table_name="daily_logs")
    op.drop_index("ix_daily_logs_user_id", table_name="daily_logs")
    op.drop_table("daily_logs")