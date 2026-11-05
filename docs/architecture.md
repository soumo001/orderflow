# OrderFlow architecture

OrderFlow is a local-only modular monolith with a separately served React frontend.

## Runtime boundaries

- `backend/app/api` exposes versioned HTTP routes.
- `backend/app/modules` owns domain models, schemas, repositories, and services.
- `backend/app/database` owns SQLAlchemy sessions and migration metadata.
- `backend/app/core` owns settings, security, logging, and cross-cutting policies.
- `backend/app/events` and `backend/app/worker` implement reliable at-least-once outbox delivery.
- `frontend/src/services` is the only frontend-to-API boundary.

PostgreSQL stores transactional state. Redis is optional and may be unavailable without preventing core API startup. Docker Compose provides only local PostgreSQL and Redis; no cloud or deployment services are part of this project.

## Domain boundaries

Authentication and authorization protect all non-public routes. Inventory reservations and order creation share a transaction and use row-level locks to prevent overselling. Payments are simulated and never accept real card information. Idempotency records protect order and payment retries. Audit records and outbox events are written in the same transaction as the business change.

