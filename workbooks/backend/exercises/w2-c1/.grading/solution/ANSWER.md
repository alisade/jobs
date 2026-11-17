# ANSWER: backend/w2-c1 Keystone core schema with tenancy enforced in the database

## Approach

Five tables with identity keys. Every tenant table carries `tenant_id` and a `UNIQUE (tenant_id, id)`
constraint; children reference parents with composite foreign keys, so a cross-tenant reference is
impossible even for the owner. Business rules are named CHECK constraints, the live-email rule is a
partial unique index on `(tenant_id, lower(email)) WHERE deleted_at IS NULL`, and `sf_id` is unique per
tenant. RLS is enabled and forced on the four tenant tables with one policy each (USING and WITH CHECK on
`current_setting('app.tenant_id', true)`), and `keystone_app` is NOLOGIN, NOBYPASSRLS, owns nothing and
has DML grants only.

## Fix

- timeline.sql: `Bitmap Index Scan on activities_timeline_idx`, Index Cond includes the RLS tenant qual,
  account_id and the row comparison. With about 12 rows per account the planner prefers a bitmap plus a
  tiny sort; for a large account it walks the index backwards and stops at 50.
- my_open_opportunities.sql: `Bitmap Index Scan on opportunities_open_by_owner_idx`; the partial index
  predicate matches the query's `stage NOT IN (...)`.
- custom_field_search.sql: `Bitmap Index Scan on accounts_tenant_sf_id_key` with
  `Filter: (custom_fields @> ...)`. The GIN index is not used: `@>` is not leakproof, so under RLS it
  cannot be evaluated before the policy qual. The planner uses an index on tenant_id and filters. Fine at
  1,250 accounts per tenant; for large tenants I would put the tenant into the indexed expression or
  move custom-field search to a search index.

Behind PgBouncer in transaction mode the services must use `set_config('app.tenant_id', $1, true)`
inside each transaction; a session `SET` would leak to the next client on that server connection.

## Trade-offs / what I would do in production

- Text tenant ids are readable and small here; with many tenants I would use a smallint/uuid key.
- CHECK for stages keeps it simple; if sales ops needs to edit stages, a lookup table per tenant.
- Partition activities by month once it passes ~100M rows; the PK must then include occurred_at.
- A CI test that fails when any table with tenant_id lacks forced RLS or a policy.
