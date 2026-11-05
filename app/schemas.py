from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    first_name: str
    last_name: str
    is_active: bool
    roles: list[str]


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    image_url: str | None = Field(default=None, max_length=500)
    category: str = Field(min_length=1, max_length=100)
    price: Decimal = Field(ge=0, decimal_places=2, max_digits=12)


class ProductUpdate(BaseModel):
    sku: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    image_url: str | None = Field(default=None, max_length=500)
    category: str | None = Field(default=None, min_length=1, max_length=100)
    price: Decimal | None = Field(default=None, ge=0, decimal_places=2, max_digits=12)
    is_active: bool | None = None


class ProductResponse(ProductCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    available_quantity: int


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    page: int
    page_size: int


class InventoryAdjustment(BaseModel):
    product_id: UUID
    quantity_delta: int
    reason: str = Field(min_length=1, max_length=100)
    reference_id: UUID | None = None

    @field_validator("quantity_delta")
    @classmethod
    def reject_zero_delta(cls, value: int) -> int:
        if value == 0:
            raise ValueError("quantity_delta must not be zero")
        return value


class InventoryResponse(BaseModel):
    product_id: UUID
    quantity: int
    reserved_quantity: int
    available_quantity: int
    low_stock_threshold: int


class MovementResponse(BaseModel):
    id: UUID
    product_id: UUID
    quantity_delta: int
    reason: str
    reference_id: UUID | None
    created_at: datetime


class OrderItemRequest(BaseModel):
    product_id: UUID
    quantity: int = Field(gt=0, le=10000)


class OrderCreateRequest(BaseModel):
    items: list[OrderItemRequest] = Field(min_length=1, max_length=100)


class OrderItemResponse(BaseModel):
    product_id: UUID
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class OrderResponse(BaseModel):
    id: UUID
    customer_id: UUID
    status: str
    subtotal: Decimal
    total: Decimal
    items: list[OrderItemResponse]
    created_at: datetime
    updated_at: datetime


class OrderStatusUpdate(BaseModel):
    status: str = Field(pattern="^(CONFIRMED|PROCESSING|SHIPPED|DELIVERED|CANCELLED)$")


class PaymentCreateRequest(BaseModel):
    order_id: UUID
    outcome: str = Field(default="success", pattern="^(success|failure|pending)$")


class PaymentResponse(BaseModel):
    id: UUID
    order_id: UUID
    amount: Decimal
    status: str
    transaction_reference: str
    created_at: datetime
