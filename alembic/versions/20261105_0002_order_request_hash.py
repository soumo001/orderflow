"""Add order request fingerprints for idempotent retries.

Revision ID: 20261105_0002
Revises: 20261105_0001
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261105_0002"
down_revision: str | None = "20261105_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("request_hash", sa.String(64), nullable=True))


def downgrade() -> None:
    op.drop_column("orders", "request_hash")
