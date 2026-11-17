# ANSWER: backend/w2-c1 Keystone core schema with tenancy enforced in the database

## Approach

<!-- How you modeled the tables: keys, how the composite foreign keys work, which rules became
CHECK / UNIQUE / partial indexes, how you set up the role and the policies. -->

## Fix

<!-- Paste the make plans output (trimmed) for each query with one sentence on why the planner chose
it. Explain the custom-field plan under RLS: which index it uses and why the GIN index is or is not
used (hint: leakproof functions and security barrier quals). -->

## Trade-offs / what I would do in production

<!-- Short. E.g. text vs uuid tenant ids, enums vs CHECK vs lookup tables, soft delete costs,
partitioning activities by month, how services set app.tenant_id behind PgBouncer, how you would
test that a new table cannot ship without RLS. -->
