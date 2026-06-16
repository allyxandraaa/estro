"""add db-level constraints to cycles table

Revision ID: b3c4d5e6f7a2
Revises: a1b2c3d4e5f6
Create Date: 2026-06-16

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b3c4d5e6f7a2"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_cycles_dates_valid",
        "cycles",
        "end_date IS NULL OR end_date >= start_date",
    )
    op.create_index(
        "uq_cycles_user_open",
        "cycles",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("end_date IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_cycles_user_open", table_name="cycles")
    op.drop_constraint("ck_cycles_dates_valid", "cycles", type_="check")
