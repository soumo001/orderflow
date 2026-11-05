from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.catalog.models import Product
from app.modules.inventory.models import Inventory
from app.schemas import ProductCreate, ProductUpdate


def get_product_or_404(db: Session, product_id: UUID) -> Product:
    product = db.scalar(select(Product).where(Product.id == product_id))
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


def create_product(db: Session, payload: ProductCreate) -> Product:
    if db.scalar(select(Product).where(Product.sku == payload.sku)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SKU already exists")
    product = Product(**payload.model_dump())
    product.inventory = Inventory(quantity=0)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product_id: UUID, payload: ProductUpdate) -> Product:
    product = get_product_or_404(db, product_id)
    changes = payload.model_dump(exclude_unset=True)
    if (
        "sku" in changes
        and changes["sku"] != product.sku
        and db.scalar(select(Product).where(Product.sku == changes["sku"])) is not None
    ):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SKU already exists")
    for field, value in changes.items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product
