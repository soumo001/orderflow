from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.api.dependencies import CurrentUser, Database, require_roles
from app.modules.orders.models import Order
from app.modules.orders.service import (
    create_order,
    get_order_or_404,
    update_order_status,
)
from app.schemas import (
    OrderCreateRequest,
    OrderItemResponse,
    OrderResponse,
    OrderStatusUpdate,
)

router = APIRouter(prefix="/orders", tags=["orders"])


def serialize_order(order: Order) -> OrderResponse:
    return OrderResponse(
        id=order.id,
        customer_id=order.customer_id,
        status=order.status,
        subtotal=order.subtotal,
        total=order.total,
        items=[
            OrderItemResponse(
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                line_total=item.unit_price * item.quantity,
            )
            for item in order.items
        ],
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order_endpoint(
    payload: OrderCreateRequest,
    db: Database,
    user: CurrentUser,
    idempotency_key: str = Header(alias="Idempotency-Key"),
) -> OrderResponse:
    return serialize_order(create_order(db, user.id, payload, idempotency_key))


@router.get("", response_model=list[OrderResponse])
def list_orders(
    db: Database,
    user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> list[OrderResponse]:
    query = select(Order).options(joinedload(Order.items)).order_by(Order.created_at.desc())
    if "ADMIN" not in {role.name for role in user.roles}:
        query = query.where(Order.customer_id == user.id)
    orders = db.scalars(query.offset((page - 1) * page_size).limit(page_size)).unique().all()
    return [serialize_order(order) for order in orders]


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: UUID, db: Database, user: CurrentUser) -> OrderResponse:
    order = get_order_or_404(db, order_id)
    if order.customer_id != user.id and "ADMIN" not in {role.name for role in user.roles}:
        require_roles("ADMIN")(user)
    return serialize_order(order)


@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    dependencies=[Depends(require_roles("ADMIN"))],
)
def change_status(
    order_id: UUID, payload: OrderStatusUpdate, db: Database
) -> OrderResponse:
    return serialize_order(update_order_status(db, order_id, payload.status))


@router.post("/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(order_id: UUID, db: Database, user: CurrentUser) -> OrderResponse:
    order = get_order_or_404(db, order_id)
    if order.customer_id != user.id and "ADMIN" not in {role.name for role in user.roles}:
        require_roles("ADMIN")(user)
    return serialize_order(update_order_status(db, order_id, "CANCELLED"))
