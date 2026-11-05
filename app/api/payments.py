from uuid import UUID

from fastapi import APIRouter, Header, status
from sqlalchemy import select

from app.api.dependencies import CurrentUser, Database
from app.modules.payments.models import Payment
from app.modules.payments.service import create_payment, refund_payment
from app.schemas import PaymentCreateRequest, PaymentResponse

router = APIRouter(prefix="/payments", tags=["payments"])


def serialize_payment(payment: Payment) -> PaymentResponse:
    return PaymentResponse(
        id=payment.id,
        order_id=payment.order_id,
        amount=payment.amount,
        status=payment.status,
        transaction_reference=payment.transaction_reference,
        created_at=payment.created_at,
    )


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def pay(
    payload: PaymentCreateRequest,
    db: Database,
    user: CurrentUser,
    idempotency_key: str = Header(alias="Idempotency-Key"),
) -> PaymentResponse:
    return serialize_payment(create_payment(db, user.id, payload, idempotency_key))


@router.get("", response_model=list[PaymentResponse])
def list_payments(db: Database, user: CurrentUser) -> list[PaymentResponse]:
    query = select(Payment).order_by(Payment.created_at.desc())
    if "ADMIN" not in {role.name for role in user.roles}:
        query = query.where(Payment.customer_id == user.id)
    return [serialize_payment(payment) for payment in db.scalars(query).all()]


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: UUID, db: Database, user: CurrentUser) -> PaymentResponse:
    payment = db.scalar(select(Payment).where(Payment.id == payment_id))
    if payment is None or (
        payment.customer_id != user.id and "ADMIN" not in {role.name for role in user.roles}
    ):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Payment not found")
    return serialize_payment(payment)


@router.post("/{payment_id}/refund", response_model=PaymentResponse)
def refund(payment_id: UUID, db: Database, user: CurrentUser) -> PaymentResponse:
    return serialize_payment(
        refund_payment(db, payment_id, user.id, "ADMIN" in {role.name for role in user.roles})
    )
