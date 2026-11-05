from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import TimestampedModel


class Payment(TimestampedModel):
    __tablename__ = "payments"
    __table_args__ = (Index("ix_payments_order_id", "order_id"),)

    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id"), nullable=False)
    customer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    transaction_reference: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
