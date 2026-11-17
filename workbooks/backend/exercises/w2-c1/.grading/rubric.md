# Rubric: backend/w2-c1 Keystone core schema with tenancy enforced in the database
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Tenancy design | 15 | Full: composite (tenant_id, id) unique keys referenced by composite FKs on every child (incl. activities.contact_id), RLS ENABLE + FORCE on all tenant tables with USING and WITH CHECK, current_setting(..., true) so a missing tenant yields zero rows, app role NOLOGIN/NOBYPASSRLS/not owner with minimal grants; ANSWER explains why set_config(..., true) matters behind a transaction pooler. Partial: RLS without FORCE or without WITH CHECK, or single-column FKs. Zero: tenancy left to WHERE clauses. |
| 3 | Constraints as business rules | 10 | Full: named CHECKs for stage, amount and closed-needs-date; partial unique index on (tenant_id, lower(email)) WHERE deleted_at IS NULL; sf_id unique per tenant; NOT NULLs where the contract implies them. Partial: rules present but in a trigger or app code. |
| 4 | Index choices and plan reading | 15 | Full: timeline index with equality columns first then (occurred_at DESC, id DESC); partial index for open opportunities whose predicate matches the query; plans quoted with a correct sentence each; correctly explains that jsonb @> is not leakproof, so under RLS the planner evaluates the policy qual first and does not use the GIN index (it uses the tenant index and filters), with an option (e.g. a leakproof-safe design, tenant inside the indexed document, or accepting the bitmap) and its cost. Partial: indexes right, explanation thin or wrong. |
| 5 | ANSWER.md trade-offs | 10 | At least three concrete production items with a position: tenant id type, partitioning activities, enum vs CHECK vs lookup table, soft-delete costs, a CI check that every new table has RLS, PgBouncer transaction mode and SET LOCAL. |
Total: 100
