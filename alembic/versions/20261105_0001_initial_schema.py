"""Create the initial OrderFlow schema.

Revision ID: 20261105_0001
Revises:
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20261105_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

uuid = postgresql.UUID(as_uuid=True)
timestamp = sa.DateTime(timezone=True)


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("id", uuid, primary_key=True),
        sa.Column("created_at", timestamp, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", timestamp, server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "roles",
        *timestamps(),
        sa.Column("name", sa.String(40), nullable=False, unique=True),
    )
    op.create_table(
        "users",
        *timestamps(),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_table(
        "user_roles",
        sa.Column("user_id", uuid, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", uuid, sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_table(
        "products",
        *timestamps(),
        sa.Column("sku", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.CheckConstraint("price >= 0", name="ck_products_price_non_negative"),
    )
    op.create_index("ix_products_category", "products", ["category"])
    op.create_table(
        "inventory",
        *timestamps(),
        sa.Column("product_id", uuid, sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reserved_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("low_stock_threshold", sa.Integer(), nullable=False, server_default="10"),
        sa.CheckConstraint("quantity >= 0", name="ck_inventory_quantity_non_negative"),
        sa.CheckConstraint("reserved_quantity >= 0", name="ck_inventory_reserved_non_negative"),
        sa.CheckConstraint("reserved_quantity <= quantity", name="ck_inventory_reserved_lte_quantity"),
    )
    op.create_table(
        "orders",
        *timestamps(),
        sa.Column("customer_id", uuid, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column("idempotency_key", sa.String(255), unique=True),
    )
    op.create_index("ix_orders_customer_id", "orders", ["customer_id"])
    op.create_table(
        "order_items",
        *timestamps(),
        sa.Column("order_id", uuid, sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", uuid, sa.ForeignKey("products.id"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),
        sa.CheckConstraint("unit_price >= 0", name="ck_order_items_unit_price_non_negative"),
    )
    op.create_table(
        "inventory_movements",
        *timestamps(),
        sa.Column("inventory_id", uuid, sa.ForeignKey("inventory.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quantity_delta", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(100), nullable=False),
        sa.Column("reference_id", uuid),
    )
    op.create_index("ix_inventory_movements_inventory_id", "inventory_movements", ["inventory_id"])
    op.create_table(
        "inventory_reservations",
        *timestamps(),
        sa.Column("inventory_id", uuid, sa.ForeignKey("inventory.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order_id", uuid, nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.CheckConstraint("quantity > 0", name="ck_reservations_quantity_positive"),
    )
    op.create_index("ix_inventory_reservations_order_id", "inventory_reservations", ["order_id"])
    op.create_table(
        "payments",
        *timestamps(),
        sa.Column("order_id", uuid, sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("customer_id", uuid, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("transaction_reference", sa.String(100), nullable=False, unique=True),
    )
    op.create_index("ix_payments_order_id", "payments", ["order_id"])
    op.create_table(
        "idempotency_keys",
        *timestamps(),
        sa.Column("key", sa.String(255), nullable=False, unique=True),
        sa.Column("user_id", uuid, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("operation", sa.String(50), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("response_status", sa.Integer()),
        sa.Column("response_body", sa.LargeBinary()),
        sa.Column("completed_at", timestamp),
    )
    op.create_table(
        "outbox_events",
        *timestamps(),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("aggregate_type", sa.String(100), nullable=False),
        sa.Column("aggregate_id", uuid, nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("available_at", timestamp, nullable=False),
        sa.Column("last_error", sa.Text()),
    )
    op.create_index("ix_outbox_events_status", "outbox_events", ["status"])
    op.create_table(
        "audit_logs",
        *timestamps(),
        sa.Column("actor_id", uuid, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", uuid),
        sa.Column("details", postgresql.JSONB()),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("user_agent", sa.Text()),
    )
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_actor_id", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_outbox_events_status", table_name="outbox_events")
    op.drop_table("outbox_events")
    op.drop_table("idempotency_keys")
    op.drop_index("ix_payments_order_id", table_name="payments")
    op.drop_table("payments")
    op.drop_index("ix_inventory_reservations_order_id", table_name="inventory_reservations")
    op.drop_table("inventory_reservations")
    op.drop_index("ix_inventory_movements_inventory_id", table_name="inventory_movements")
    op.drop_table("inventory_movements")
    op.drop_table("order_items")
    op.drop_index("ix_orders_customer_id", table_name="orders")
    op.drop_table("orders")
    op.drop_table("inventory")
    op.drop_index("ix_products_category", table_name="products")
    op.drop_table("products")
    op.drop_table("user_roles")
    op.drop_table("users")
    op.drop_table("roles")
