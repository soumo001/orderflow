# Database design

The database uses UUID primary keys and UTC timestamps.

Core tables:

1. `roles`
2. `users`
3. `user_roles`
4. `products`
5. `inventory`
6. `inventory_reservations`
7. `inventory_movements`
8. `orders`
9. `order_items`
10. `payments`
11. `idempotency_keys`
12. `outbox_events`
13. `audit_logs`

Prices and totals use PostgreSQL `NUMERIC`; floating point values are not used for financial calculations. Foreign keys, unique constraints, state checks, and indexes will be added with the domain migrations in Phase 2.

