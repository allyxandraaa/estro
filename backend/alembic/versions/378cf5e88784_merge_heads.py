"""merge heads

Revision ID: 378cf5e88784
Revises: c1d2e3f4a5b6, b3c4d5e6f7a2
Create Date: 2026-06-18 22:11:18.770372

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '378cf5e88784'
down_revision: Union[str, None] = ('c1d2e3f4a5b6', 'b3c4d5e6f7a2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
