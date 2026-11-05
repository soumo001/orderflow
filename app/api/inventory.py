from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.api.dependencies import Database, require_roles
from app.modules.inventory.models import Inventory, InventoryMovement
from app.modules.inventory.service import adjust_inventory
from app.schemas import InventoryAdjustment, InventoryResponse, MovementResponse

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(require_roles("ADMIN", "INVENTORY_MANAGER"))],
)


def serialize_inventory(inventory: Inventory) -> InventoryResponse:
    return InventoryResponse(
        product_id=inventory.product_id,
        quantity=inventory.quantity,
        reserved_quantity=inventory.reserved_quantity,
        available_quantity=inventory.available_quantity,
        low_stock_threshold=inventory.low_stock_threshold,
    )


@router.get("", response_model=list[InventoryResponse])
def list_inventory(db: Database) -> list[InventoryResponse]:
    inventories = db.scalars(select(Inventory).order_by(Inventory.updated_at.desc())).all()
    return [serialize_inventory(inventory) for inventory in inventories]


@router.get("/low-stock", response_model=list[InventoryResponse])
def low_stock(db: Database) -> list[InventoryResponse]:
    inventories = db.scalars(
        select(Inventory).where(
            Inventory.quantity - Inventory.reserved_quantity <= Inventory.low_stock_threshold
        )
    ).all()
    return [serialize_inventory(inventory) for inventory in inventories]


@router.post("/adjustments", response_model=InventoryResponse, status_code=status.HTTP_200_OK)
def adjust_stock(payload: InventoryAdjustment, db: Database) -> InventoryResponse:
    return serialize_inventory(
        adjust_inventory(db, payload.product_id, payload.quantity_delta, payload.reason, payload.reference_id)
    )


@router.get("/movements", response_model=list[MovementResponse])
def movements(
    db: Database,
    product_id: UUID | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[MovementResponse]:
    query = (
        select(InventoryMovement)
        .options(joinedload(InventoryMovement.inventory))
        .order_by(InventoryMovement.created_at.desc())
        .limit(limit)
    )
    if product_id:
        query = query.join(Inventory).where(Inventory.product_id == product_id)
    records = db.scalars(query).unique().all()
    return [
        MovementResponse(
            id=record.id,
            product_id=record.inventory.product_id,
            quantity_delta=record.quantity_delta,
            reason=record.reason,
            reference_id=record.reference_id,
            created_at=record.created_at,
        )
        for record in records
    ]
