from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from app.api.dependencies import Database, require_roles
from app.modules.audit.models import AuditLog
from app.modules.catalog.models import Product
from app.modules.events import process_pending_events
from app.modules.inventory.models import Inventory
from app.modules.orders.models import Order
from app.modules.outbox.models import OutboxEvent
from app.modules.payments.models import Payment
from app.modules.users.models import User

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_roles("ADMIN"))])


@router.get("/dashboard")
def dashboard(db: Database) -> dict:
    revenue = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.status == "SUCCEEDED")
    )
    return {
        "total_revenue": revenue,
        "total_orders": db.scalar(select(func.count(Order.id))) or 0,
        "total_customers": db.scalar(select(func.count(User.id))) or 0,
        "total_products": db.scalar(select(func.count(Product.id))) or 0,
        "pending_orders": db.scalar(select(func.count(Order.id)).where(Order.status == "PENDING")) or 0,
        "low_stock_products": db.scalar(
            select(func.count(Inventory.id)).where(
                Inventory.quantity - Inventory.reserved_quantity <= Inventory.low_stock_threshold
            )
        ) or 0,
    }


@router.get("/users")
def users(db: Database) -> list[dict]:
    return [
        {"id": user.id, "email": user.email, "first_name": user.first_name, "last_name": user.last_name, "is_active": user.is_active}
        for user in db.scalars(select(User).order_by(User.created_at.desc())).all()
    ]


@router.get("/audit-logs")
def audit_logs(db: Database, limit: int = 100) -> list[dict]:
    records = db.scalars(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(min(limit, 500))
    ).all()
    return [
        {
            "id": record.id,
            "actor_id": record.actor_id,
            "action": record.action,
            "entity_type": record.entity_type,
            "entity_id": record.entity_id,
            "details": record.details,
            "created_at": record.created_at,
        }
        for record in records
    ]


@router.get("/events")
def events(db: Database, limit: int = 100) -> list[dict]:
    records = db.scalars(
        select(OutboxEvent).order_by(OutboxEvent.created_at.desc()).limit(min(limit, 500))
    ).all()
    return [
        {
            "id": event.id,
            "event_type": event.event_type,
            "aggregate_type": event.aggregate_type,
            "aggregate_id": event.aggregate_id,
            "status": event.status,
            "attempts": event.attempts,
            "last_error": event.last_error,
            "created_at": event.created_at,
        }
        for event in records
    ]


@router.get("/events/dead-letter")
def dead_letter(db: Database) -> list[dict]:
    records = db.scalars(select(OutboxEvent).where(OutboxEvent.status == "DEAD_LETTER")).all()
    return [
        {
            "id": event.id,
            "event_type": event.event_type,
            "status": event.status,
            "attempts": event.attempts,
            "last_error": event.last_error,
        }
        for event in records
    ]


@router.post("/events/process")
def process_events(db: Database) -> dict[str, int]:
    return {"processed": process_pending_events(db)}
