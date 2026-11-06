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

The frontend reads `VITE_API_BASE_URL` when Vite builds the application. Use
`http://localhost:8000` locally and set it to
`https://orderflow-zo5f.onrender.com` in the Render frontend environment.
Changing this variable requires a new frontend build and redeployment; it is
not read dynamically by the browser at runtime.

API reference: [docs/api.md](docs/api.md)

## Render deployment configuration

Set these backend environment variables in the Render API service:

```text
ENVIRONMENT=production
DATABASE_URL=<Render PostgreSQL connection string>
JWT_SECRET_KEY=<random secret of at least 16 characters>
FRONTEND_ORIGINS=http://localhost:5173,https://orderflow-frontend-lkno.onrender.com
```

Set this frontend environment variable in the Render static site before its
build:

```text
VITE_API_BASE_URL=https://orderflow-zo5f.onrender.com
```

Use `alembic upgrade head` as the backend pre-deploy command, then start the
API with `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Build the frontend
with `npm install && npm run build` and publish `frontend/dist`. Changing
`VITE_API_BASE_URL` requires a new frontend build and redeployment.

After both services deploy, verify `/health`, `/ready`, and
`/api/v1/products?page_size=1` directly. A successful health response does not
prove that PostgreSQL is reachable; the product request must also succeed.

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
