import hashlib
import json
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.modules.catalog.models import Product
from app.modules.events import enqueue_event, record_audit
from app.modules.inventory.models import Inventory, InventoryMovement, InventoryReservation
from app.modules.orders.models import Order, OrderItem
from app.schemas import OrderCreateRequest

ORDER_TRANSITIONS: dict[str, set[str]] = {
    "PENDING": {"CONFIRMED", "CANCELLED"},
    "CONFIRMED": {"PROCESSING", "CANCELLED"},
    "PROCESSING": {"SHIPPED", "CANCELLED"},
    "SHIPPED": {"DELIVERED"},
    "DELIVERED": set(),
    "CANCELLED": set(),
}


def request_hash(payload: OrderCreateRequest) -> str:
    canonical = [
        {"product_id": str(item.product_id), "quantity": item.quantity}
        for item in sorted(payload.items, key=lambda item: str(item.product_id))
    ]
    return hashlib.sha256(json.dumps(canonical, separators=(",", ":")).encode()).hexdigest()


def get_order_or_404(db: Session, order_id: UUID, *, lock: bool = False) -> Order:
    query = select(Order).options(joinedload(Order.items)).where(Order.id == order_id)
    if lock:
        query = query.with_for_update()
    order = db.scalar(query)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


def create_order(
    db: Session, customer_id: UUID, payload: OrderCreateRequest, idempotency_key: str
) -> Order:
    if not idempotency_key.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Idempotency key is required")
    fingerprint = request_hash(payload)
    existing = db.scalar(select(Order).where(Order.idempotency_key == idempotency_key))
    if existing is not None:
        if existing.request_hash != fingerprint:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Idempotency key was already used with a different request",
            )
        return get_order_or_404(db, existing.id)

    quantities: dict[UUID, int] = {}
    for item in payload.items:
        quantities[item.product_id] = quantities.get(item.product_id, 0) + item.quantity

    products = db.scalars(
        select(Product).where(Product.id.in_(quantities), Product.is_active.is_(True))
    ).all()
    products_by_id = {product.id: product for product in products}
    if len(products_by_id) != len(quantities):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more products not found")

    inventories = db.scalars(
        select(Inventory)
        .where(Inventory.product_id.in_(quantities))
        .with_for_update()
    ).all()
    inventory_by_product = {inventory.product_id: inventory for inventory in inventories}
    if len(inventory_by_product) != len(quantities):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Product inventory is unavailable")

    for product_id, quantity in quantities.items():
        if inventory_by_product[product_id].available_quantity < quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Insufficient stock for product {product_id}",
            )

    order = Order(
        customer_id=customer_id,
        status="PENDING",
        subtotal=Decimal(0),
        total=Decimal(0),
        idempotency_key=idempotency_key,
        request_hash=fingerprint,
    )
    db.add(order)
    db.flush()
    subtotal = Decimal(0)
    for product_id, quantity in quantities.items():
        product = products_by_id[product_id]
        line_total = product.price * quantity
        subtotal += line_total
        order.items.append(
            OrderItem(product_id=product_id, quantity=quantity, unit_price=product.price)
        )
        inventory = inventory_by_product[product_id]
        inventory.reserved_quantity += quantity
        db.add(
            InventoryReservation(
                inventory_id=inventory.id,
                order_id=order.id,
                quantity=quantity,
                status="ACTIVE",
            )
        )
        db.add(
            InventoryMovement(
                inventory_id=inventory.id,
                quantity_delta=0,
                reason="ORDER_RESERVED",
                reference_id=order.id,
            )
        )
    order.subtotal = subtotal
    order.total = subtotal
    record_audit(db, "ORDER_CREATED", "order", order.id, customer_id)
    enqueue_event(
        db,
        "order.created",
        "order",
        order.id,
        {"order_id": str(order.id), "customer_id": str(customer_id)},
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(select(Order).where(Order.idempotency_key == idempotency_key))
        if existing is None:
            raise
        if existing.request_hash != fingerprint:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Idempotency key was already used with a different request",
            ) from None
        return get_order_or_404(db, existing.id)
    return get_order_or_404(db, order.id)


def update_order_status(db: Session, order_id: UUID, next_status: str) -> Order:
    order = get_order_or_404(db, order_id, lock=True)
    if next_status not in ORDER_TRANSITIONS.get(order.status, set()):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot transition order from {order.status} to {next_status}",
        )
    if next_status == "CANCELLED":
        release_order_reservations(db, order)
    order.status = next_status
    record_audit(db, "ORDER_STATUS_UPDATED", "order", order.id, None, {"status": next_status})
    enqueue_event(
        db,
        "order.status_changed",
        "order",
        order.id,
        {"order_id": str(order.id), "status": next_status},
    )
    db.commit()
    return get_order_or_404(db, order.id)


def release_order_reservations(db: Session, order: Order) -> None:
    reservations = db.scalars(
        select(InventoryReservation)
        .where(InventoryReservation.order_id == order.id, InventoryReservation.status == "ACTIVE")
        .with_for_update()
    ).all()
    for reservation in reservations:
        inventory = db.scalar(
            select(Inventory).where(Inventory.id == reservation.inventory_id).with_for_update()
        )
        if inventory is None:
            continue
        inventory.reserved_quantity -= reservation.quantity
        reservation.status = "RELEASED"
        db.add(
            InventoryMovement(
                inventory_id=inventory.id,
                quantity_delta=0,
                reason="ORDER_RESERVATION_RELEASED",
                reference_id=order.id,
            )
        )
