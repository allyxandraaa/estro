"""add last_period_date to users

Revision ID: b4e91c2d3f07
Revises: 93dc96f56486
Create Date: 2026-06-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b4e91c2d3f07'
down_revision: Union[str, None] = '93dc96f56486'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('last_period_date', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'last_period_date')
