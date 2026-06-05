"""add last_period_date and is_calculated_default to users

Revision ID: a1b2c3d4e5f6
Revises: 93dc96f56486
Create Date: 2026-06-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '93dc96f56486'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('last_period_date', sa.Date(), nullable=True),
    )
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
    op.drop_column('users', 'last_period_date')