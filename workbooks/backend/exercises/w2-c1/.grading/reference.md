# Reference: backend/w2-c1

The reference migration is `.grading/solution/migrations/0001_core.sql`.

## Key decisions

- **Composite keys for tenancy.** Each parent has `UNIQUE (tenant_id, id)`; each child has
  `FOREIGN KEY (tenant_id, account_id) REFERENCES accounts (tenant_id, id)`. A row whose tenant differs
  from its parent's cannot exist, whoever writes it. RLS alone does not give you this: the owner and
  migration jobs bypass or sidestep it, and RLS does not apply to FK checks.
- **FORCE ROW LEVEL SECURITY.** Without FORCE the table owner bypasses policies. Services should not
  connect as the owner anyway, but FORCE closes the gap for jobs that do.
- **`current_setting('app.tenant_id', true)`**: the `missing_ok` flag returns NULL instead of an error,
  and `tenant_id = NULL` is never true, so a forgotten tenant gives zero rows (fail closed).
- **`set_config(..., true)` per transaction**: transaction-local, so behind PgBouncer in transaction mode
  the setting cannot leak onto the next client's transaction on the same server connection. A plain
  `SET` would.
- **`keystone_app NOLOGIN NOBYPASSRLS`**: login roles (one per service) are granted membership; the
  app role owns nothing.
- **Partial unique index** `(tenant_id, lower(email)) WHERE deleted_at IS NULL`: soft delete breaks
  plain UNIQUE constraints; this is the standard fix.
- **Timeline index** `(tenant_id, account_id, occurred_at DESC, id DESC)`: equality columns first, then
  the ORDER BY columns in order, so a keyset page is a short index range. The planner may still choose a
  bitmap scan plus a small sort when the account has few rows; with a large account it walks the index
  in order and stops at 50.
- **Open-opportunity partial index** with the same `stage NOT IN (...)` predicate as the query; the
  planner only uses a partial index when the query predicate implies the index predicate.

## The GIN index under RLS

`jsonb @>` (`jsonb_contains`) is not marked LEAKPROOF. With RLS the policy qual acts as a security
barrier: quals from the user query that are not leakproof must be evaluated after the policy, so they
cannot be pushed into an index scan that would run before it. The plan therefore uses the tenant index
(any index with `tenant_id` first) and filters `custom_fields @> ...` per row. Options: accept it while
tenants are small; put the tenant into the indexed expression (for example an expression GIN index over
`jsonb_build_object('t', tenant_id) || custom_fields` and query with the same expression, or btree_gin
for a `(tenant_id, custom_fields)` GIN index, where the extension is available); move custom-field
search to a search index; or, as a last resort and with a security review, a SECURITY DEFINER function.
Marking `jsonb_contains` leakproof is not acceptable: only a superuser can, and it is wrong in general.

## Interview angles

- "Why not schema-per-tenant?" Cost and migration fan-out versus isolation and noisy neighbors.
- "How do you know a new table has RLS?" A CI check over `pg_class.relrowsecurity/relforcerowsecurity`
  for every table with a `tenant_id` column, plus a test that queries it as the app role with no tenant.
- "What breaks with PgBouncer?" Session state: `SET`, advisory locks, prepared statements in older
  versions. `set_config(..., true)` inside the transaction is the safe pattern.
