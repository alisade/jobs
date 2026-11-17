# ADR 0001: Tenancy model

## Status

Accepted for phase 1.

## Context

Six tenants (business units and apps) share one CRM org today, separated by sharing rules. Volumes are
modest except activities. EMEA has two regulated customers whose data must stay in the EU. Partner
managers legitimately read partner accounts across tenants. Agents must get exactly the user's access.

## Options

1. Shared schema, `tenant_id` on every row, Postgres RLS. Cheapest, one migration path, cross-tenant
   partner reads are a policy. Risk: one bad query or a missing policy exposes data; noisy neighbors
   share one database.
2. Schema per tenant. Stronger separation, per-tenant restore. Migrations run six times (and N times as
   apps onboard), cross-tenant partner reads need UNION views, connection pools multiply.
3. Database per tenant. Strongest isolation and placement per region. Highest cost and operational
   load; cross-tenant queries move to the warehouse; overkill for internal business units.
4. Hybrid: option 1 per region, with tenant-to-region placement (the EU tenant in an EU deployment).

## Decision

Option 4: shared schema with RLS (ENABLE and FORCE, app roles without BYPASSRLS, `SET LOCAL` of the
tenant per transaction), one deployment per region, tenants placed by region.

## Consequences

- A CI check fails any migration that adds a tenant table without RLS policies; an integration test
  connects as the app role without a tenant and must see zero rows.
- Every pooled connection path must set the tenant inside the transaction (PgBouncer transaction mode).
- Noisy neighbor protection comes from per-tenant quotas at the API, not from the database.
- Moving a tenant between regions is a data migration project, accepted because it is rare.
