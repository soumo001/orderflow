from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import TimestampedModel

if TYPE_CHECKING:
    from app.modules.catalog.models import Product


class Inventory(TimestampedModel):
    __tablename__ = "inventory"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_inventory_quantity_non_negative"),
        CheckConstraint("reserved_quantity >= 0", name="ck_inventory_reserved_non_negative"),
        CheckConstraint("reserved_quantity <= quantity", name="ck_inventory_reserved_lte_quantity"),
    )

    product_id: Mapped[UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    product: Mapped["Product"] = relationship(back_populates="inventory")
    movements: Mapped[list["InventoryMovement"]] = relationship(back_populates="inventory")
    reservations: Mapped[list["InventoryReservation"]] = relationship(back_populates="inventory")

    @property
    def available_quantity(self) -> int:
        return self.quantity - self.reserved_quantity


class InventoryMovement(TimestampedModel):
    __tablename__ = "inventory_movements"
    __table_args__ = (Index("ix_inventory_movements_inventory_id", "inventory_id"),)

    inventory_id: Mapped[UUID] = mapped_column(
        ForeignKey("inventory.id", ondelete="CASCADE"), nullable=False
    )
    quantity_delta: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(100), nullable=False)
    reference_id: Mapped[UUID | None] = mapped_column()
    inventory: Mapped[Inventory] = relationship(back_populates="movements")


class InventoryReservation(TimestampedModel):
    __tablename__ = "inventory_reservations"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_reservations_quantity_positive"),
        Index("ix_inventory_reservations_order_id", "order_id"),
    )

    inventory_id: Mapped[UUID] = mapped_column(
        ForeignKey("inventory.id", ondelete="CASCADE"), nullable=False
    )
    order_id: Mapped[UUID] = mapped_column(nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)
    inventory: Mapped[Inventory] = relationship(back_populates="reservations")
