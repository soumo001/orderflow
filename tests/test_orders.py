from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.orders.service import ORDER_TRANSITIONS, request_hash
from app.schemas import InventoryAdjustment, OrderCreateRequest, OrderItemRequest


def test_order_request_hash_is_order_independent() -> None:
    first = OrderCreateRequest(
        items=[
            OrderItemRequest(product_id=uuid4(), quantity=1),
            OrderItemRequest(product_id=uuid4(), quantity=2),
        ]
    )
    second = OrderCreateRequest(items=list(reversed(first.items)))

    assert request_hash(first) == request_hash(second)


def test_order_status_transitions_are_restricted() -> None:
    assert ORDER_TRANSITIONS["PENDING"] == {"CONFIRMED", "CANCELLED"}
    assert ORDER_TRANSITIONS["DELIVERED"] == set()


def test_zero_inventory_adjustment_is_invalid() -> None:
    with pytest.raises(ValidationError):
        InventoryAdjustment(product_id=uuid4(), quantity_delta=0, reason="test")
