import hashlib
import json
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.events import enqueue_event, record_audit
from app.modules.orders.models import Order
from app.modules.payments.models import Payment
from app.schemas import PaymentCreateRequest


def payment_hash(payload: PaymentCreateRequest) -> str:
    data = {"order_id": str(payload.order_id), "outcome": payload.outcome}
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def create_payment(db: Session, customer_id: UUID, payload: PaymentCreateRequest, key: str) -> Payment:
    if not key.strip():
        raise HTTPException(status_code=400, detail="Idempotency key is required")
    fingerprint = payment_hash(payload)
    existing = db.scalar(select(Payment).where(Payment.idempotency_key == key))
    if existing is not None:
        if existing.request_hash != fingerprint:
            raise HTTPException(status_code=409, detail="Payment key was reused with a different request")
        return existing
    order = db.scalar(select(Order).where(Order.id == payload.order_id, Order.customer_id == customer_id))
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status == "CANCELLED":
        raise HTTPException(status_code=409, detail="Cancelled orders cannot be paid")
    payment = Payment(
        order_id=order.id,
        customer_id=customer_id,
        amount=order.total,
        status=(
            "SUCCEEDED"
            if payload.outcome == "success"
            else "FAILED"
            if payload.outcome == "failure"
            else "PENDING"
        ),
        transaction_reference=f"sim_{uuid4().hex}",
        idempotency_key=key,
        request_hash=fingerprint,
    )
    db.add(payment)
    if payment.status == "SUCCEEDED" and order.status == "PENDING":
        order.status = "CONFIRMED"
    db.flush()
    record_audit(db, "PAYMENT_CREATED", "payment", payment.id, customer_id, {"status": payment.status})
    enqueue_event(
        db,
        "payment.created",
        "payment",
        payment.id,
        {"payment_id": str(payment.id), "status": payment.status},
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(select(Payment).where(Payment.idempotency_key == key))
        if existing is None:
            raise
        if existing.request_hash != fingerprint:
            raise HTTPException(status_code=409, detail="Payment key was reused with a different request")
        return existing
    db.refresh(payment)
    return payment


def refund_payment(db: Session, payment_id: UUID, customer_id: UUID, is_admin: bool) -> Payment:
    payment = db.scalar(select(Payment).where(Payment.id == payment_id))
    if payment is None or (payment.customer_id != customer_id and not is_admin):
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.status != "SUCCEEDED":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only successful payments can be refunded")
    payment.status = "REFUNDED"
    record_audit(db, "PAYMENT_REFUNDED", "payment", payment.id, customer_id)
    enqueue_event(db, "payment.refunded", "payment", payment.id, {"payment_id": str(payment.id)})
    db.commit()
    db.refresh(payment)
    return payment
