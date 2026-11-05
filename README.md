# OrderFlow

OrderFlow is a local-first order and inventory management platform.

## Implementation status

All planned local development phases are implemented: normalized PostgreSQL schema and seed data, JWT/RBAC authentication, catalogue and inventory APIs, transactional orders and reservations, simulated payments and refunds, audit/outbox processing, admin metrics, and an integrated React catalogue/cart/checkout frontend.

## Local prerequisites

- Python 3.12+
- Node.js LTS
- Docker Desktop (for the optional local PostgreSQL and Redis containers)

## Start the Phase 1 baseline

```powershell
docker compose up -d
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

In another PowerShell terminal:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

- Backend: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Frontend: http://localhost:5173

API reference: [docs/api.md](docs/api.md)

Run the baseline backend tests from the repository root:

```powershell
pytest
```

Seed the local database after applying migrations:

```powershell
alembic upgrade head
python -m app.seed
```

Run the transactional outbox worker in a separate terminal:

```powershell
python -m app.worker.runner
```

The worker uses PostgreSQL row locking and processes pending events with retry
backoff. Events that exceed five attempts are marked `DEAD_LETTER` and are
visible to administrators through `/api/v1/admin/events/dead-letter`.

Development accounts:

| Role | Email | Password |
|---|---|---|
| Admin | `admin@orderflow.local` | `Admin123!` |
| Inventory manager | `inventory@orderflow.local` | `Inventory123!` |
| Customer | `customer1@orderflow.local` | `Customer123!` |
| Customer | `customer2@orderflow.local` | `Customer123!` |

## Completed feature checklist

- [x] Registration, login, refresh, logout, and current-user lookup
- [x] Admin, inventory-manager, and customer roles
- [x] Product search, filtering, sorting, pagination, and admin mutations
- [x] Inventory adjustments, low-stock reporting, movements, and reservations
- [x] Transactional order creation, cancellation, lifecycle transitions, and ownership checks
- [x] Order and payment idempotency keys
- [x] Simulated success, failure, pending, and refund payment flows
- [x] Audit logs, transactional outbox, retries, dead-letter visibility, and worker
- [x] Admin dashboard metrics and event/user endpoints
- [x] React catalogue, registration/login, cart, checkout, orders, and admin metrics
