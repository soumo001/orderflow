"""Add payment idempotency fields.

Revision ID: 20261105_0003
Revises: 20261105_0002
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261105_0003"
down_revision: str | None = "20261105_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("payments", sa.Column("idempotency_key", sa.String(255), nullable=True))
    op.add_column("payments", sa.Column("request_hash", sa.String(64), nullable=True))
    op.create_unique_constraint("uq_payments_idempotency_key", "payments", ["idempotency_key"])


def downgrade() -> None:
    op.drop_constraint("uq_payments_idempotency_key", "payments", type_="unique")
    op.drop_column("payments", "request_hash")
    op.drop_column("payments", "idempotency_key")
