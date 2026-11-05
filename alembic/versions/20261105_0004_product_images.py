"""Add product image URLs.

Revision ID: 20261105_0004
Revises: 20261105_0003
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261105_0004"
down_revision: str | None = "20261105_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("products", sa.Column("image_url", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("products", "image_url")
