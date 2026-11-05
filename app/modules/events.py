from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.audit.models import AuditLog
from app.modules.outbox.models import OutboxEvent


def record_audit(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: UUID | None,
    actor_id: UUID | None,
    details: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            details=details,
        )
    )


def enqueue_event(
    db: Session,
    event_type: str,
    aggregate_type: str,
    aggregate_id: UUID,
    payload: dict,
) -> None:
    db.add(
        OutboxEvent(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=payload,
            status="PENDING",
            available_at=datetime.now(UTC),
        )
    )


def process_pending_events(db: Session, limit: int = 50) -> int:
    events = db.scalars(
        select(OutboxEvent)
        .where(
            OutboxEvent.status == "PENDING",
            OutboxEvent.available_at <= datetime.now(UTC),
        )
        .with_for_update(skip_locked=True)
        .limit(limit)
    ).all()
    processed = 0
    for event in events:
        try:
            event.status = "PROCESSED"
            event.attempts += 1
            event.last_error = None
            processed += 1
        except (RuntimeError, ValueError) as exc:
            event.attempts += 1
            event.last_error = str(exc)
            event.status = "DEAD_LETTER" if event.attempts >= 5 else "PENDING"
            event.available_at = datetime.now(UTC) + timedelta(seconds=2**event.attempts)
    db.commit()
    return processed
