"""add name to users

Revision ID: d6a7b8c9e0f1
Revises: c5d8e9f0a1b2
Create Date: 2026-06-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d6a7b8c9e0f1"
down_revision: Union[str, None] = "c5d8e9f0a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("name", sa.String(length=255), nullable=True))
    op.execute(
        "UPDATE users SET name = NULLIF(regexp_replace(email, '@.*$', ''), '') "
        "WHERE name IS NULL OR name = ''"
    )
    op.alter_column("users", "name", existing_type=sa.String(length=255), nullable=False)


def downgrade() -> None:
    op.drop_column("users", "name")
