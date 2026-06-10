"""repair partial profile defaults

Revision ID: e1f2a3b4c5d6
Revises: d6a7b8c9e0f1
Create Date: 2026-06-10

"""
from typing import Sequence, Union

from alembic import op


revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, None] = "d6a7b8c9e0f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE users
        SET average_period_length = 5,
            is_calculated_default = true
        WHERE average_cycle_length IS NOT NULL
          AND average_period_length IS NULL
        """
    )
    op.execute(
        """
        UPDATE users
        SET average_cycle_length = 28,
            is_calculated_default = true
        WHERE average_cycle_length IS NULL
          AND average_period_length IS NOT NULL
        """
    )


def downgrade() -> None:
    pass
