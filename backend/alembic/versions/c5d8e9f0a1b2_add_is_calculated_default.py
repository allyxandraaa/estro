"""add is_calculated_default to users

Revision ID: c5d8e9f0a1b2
Revises: b4e91c2d3f07
Create Date: 2026-06-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c5d8e9f0a1b2'
down_revision: Union[str, None] = 'b4e91c2d3f07'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column(
            'is_calculated_default',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false'),
        ),
    )


def downgrade() -> None:
    op.drop_column('users', 'is_calculated_default')
