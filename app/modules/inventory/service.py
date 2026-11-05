from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.events import record_audit
from app.modules.inventory.models import Inventory, InventoryMovement


def get_inventory_or_404(db: Session, product_id: UUID, *, lock: bool = False) -> Inventory:
    query = select(Inventory).where(Inventory.product_id == product_id)
    if lock:
        query = query.with_for_update()
    inventory = db.scalar(query)
    if inventory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory not found")
    return inventory


def adjust_inventory(
    db: Session, product_id: UUID, quantity_delta: int, reason: str, reference_id: UUID | None
) -> Inventory:
    inventory = get_inventory_or_404(db, product_id, lock=True)
    new_quantity = inventory.quantity + quantity_delta
    if new_quantity < inventory.reserved_quantity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Adjustment cannot reduce stock below reserved quantity",
        )
    inventory.quantity = new_quantity
    db.add(
        InventoryMovement(
            inventory_id=inventory.id,
            quantity_delta=quantity_delta,
            reason=reason,
            reference_id=reference_id,
        )
    )
    record_audit(
        db,
        "INVENTORY_ADJUSTED",
        "inventory",
        inventory.id,
        None,
        {"quantity_delta": quantity_delta, "reason": reason},
    )
    db.commit()
    db.refresh(inventory)
    return inventory
