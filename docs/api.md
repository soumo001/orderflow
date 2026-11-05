# OrderFlow API

The API is versioned under `/api/v1` and documented interactively at
`http://localhost:8000/docs`.

## Public endpoints

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `GET /products`
- `GET /products/{product_id}`

## Authenticated customer endpoints

- `GET /auth/me`
- `POST /auth/logout`
- `POST /orders` with an `Idempotency-Key` header
- `GET /orders`
- `GET /orders/{order_id}`
- `POST /orders/{order_id}/cancel`
- `POST /payments` with an `Idempotency-Key` header
- `GET /payments`
- `GET /payments/{payment_id}`
- `POST /payments/{payment_id}/refund`

## Admin and inventory endpoints

- Product mutations require `ADMIN`.
- Inventory endpoints require `ADMIN` or `INVENTORY_MANAGER`.
- `/admin/*` endpoints require `ADMIN`.
- Inventory adjustments, order creation, payments, refunds, and status changes
  create audit/outbox records in the same database transaction.

## Local payment simulation

Payment requests accept `outcome` values of `success`, `failure`, or `pending`.
No card data or real payment gateway is used.

