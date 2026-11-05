from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import TimestampedModel


class IdempotencyKey(TimestampedModel):
    __tablename__ = "idempotency_keys"

    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    operation: Mapped[str] = mapped_column(String(50), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    response_status: Mapped[int | None] = mapped_column()
    response_body: Mapped[bytes | None] = mapped_column(LargeBinary)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

