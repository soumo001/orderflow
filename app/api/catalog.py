from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.api.dependencies import Database, require_roles
from app.modules.catalog.models import Product
from app.modules.catalog.service import create_product, get_product_or_404, update_product
from app.schemas import ProductCreate, ProductListResponse, ProductResponse, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])
admin_only = Depends(require_roles("ADMIN"))


def serialize_product(product: Product) -> ProductResponse:
    inventory = product.inventory
    return ProductResponse(
        id=product.id,
        sku=product.sku,
        name=product.name,
        description=product.description,
        image_url=product.image_url,
        category=product.category,
        price=product.price,
        is_active=product.is_active,
        available_quantity=inventory.available_quantity if inventory else 0,
    )


@router.get("", response_model=ProductListResponse)
def list_products(
    db: Database,
    search: str | None = Query(default=None, min_length=1, max_length=100),
    category: str | None = Query(default=None, max_length=100),
    sort: str = Query(default="created_at", pattern="^(created_at|price)$"),
    descending: bool = True,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ProductListResponse:
    query = (
        select(Product)
        .options(joinedload(Product.inventory))
        .where(Product.is_active.is_(True))
    )
    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))
    if category:
        query = query.where(Product.category == category)
    sort_column = Product.price if sort == "price" else Product.created_at
    order_column = sort_column.desc() if descending else sort_column.asc()
    products = db.scalars(
        query.order_by(order_column)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).unique().all()
    return ProductListResponse(items=[serialize_product(product) for product in products], page=page, page_size=page_size)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: UUID, db: Database) -> ProductResponse:
    product = get_product_or_404(db, product_id)
    if not product.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    product = db.scalar(
        select(Product)
        .options(joinedload(Product.inventory))
        .where(Product.id == product_id)
    )
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return serialize_product(product)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[admin_only],
)
def create_product_endpoint(payload: ProductCreate, db: Database) -> ProductResponse:
    return serialize_product(create_product(db, payload))


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    dependencies=[admin_only],
)
def update_product_endpoint(
    product_id: UUID, payload: ProductUpdate, db: Database
) -> ProductResponse:
    return serialize_product(update_product(db, product_id, payload))


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[admin_only],
)
def deactivate_product(product_id: UUID, db: Database) -> None:
    product = get_product_or_404(db, product_id)
    product.is_active = False
    db.commit()
