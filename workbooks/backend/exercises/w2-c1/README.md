# backend/w2-c1 - Keystone core schema with tenancy enforced in the database

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 2 (Mon: modeling and constraints; Tue: indexes; Wed: reading plans; Thu: row-level security for tenancy)

## Scenario

Lumenfold is replacing its third-party CRM with Keystone. The accounts-svc and pipeline-svc teams
share one PostgreSQL cluster and agreed on the core tables in a whiteboard session; you own the first
migration. Two requirements came out of the security review and are not negotiable:

- Tenancy (a tenant is a business unit or an internal app: `bu-amer`, `bu-emea`, `bu-apac`,
  `app-partner-portal`) is enforced **by the database**, not by every developer remembering a
  `WHERE tenant_id = ...`. A service that forgets to set the tenant must see nothing, not everything.
- Agentic apps will query through the same services (Keystone MCP tools), so the rules that used to
  live in CRM validation rules have to be constraints, not application code that an agent can route around.

The services connect as role `keystone_app` and set the tenant per transaction with
`SELECT set_config('app.tenant_id', $1, true)` (the `true` makes it transaction-local, like
`SET LOCAL`, which is what keeps it from leaking between requests behind a transaction pooler).

## What you have

| Path | What it is |
|---|---|
| `migrations/0001_core.sql` | the starter migration: `tenants` and a bare `accounts`, TODOs for the rest |
| `queries/*.sql` | the three hot queries the services run (do not change them) |
| `tests/harness.ts` | applies `migrations/` to a fresh in-process PostgreSQL 18 (PGlite) and seeds 5k accounts, 10k contacts, 12k opportunities, 60k activities |
| `tests/schema.test.ts` | visible tests |
| `scripts/plans.js` | `make plans`: `EXPLAIN (ANALYZE, BUFFERS)` of each query as `keystone_app` for `bu-emea` |

You may split the schema into several files (`0001_*.sql`, `0002_*.sql`, ...); they apply in lexical order.

## Requirements

Column contract (names the services and tests use):

- `tenants (id text PK, name)`
- `accounts (id, tenant_id, name, owner_id, sf_id, custom_fields jsonb, created_at)`
- `contacts (id, tenant_id, account_id, first_name, last_name, email, sf_id, deleted_at, created_at)`
- `opportunities (id, tenant_id, account_id, owner_id, name, stage, amount, close_date, sf_id, created_at)`
- `activities (id, tenant_id, account_id, contact_id (nullable), type, subject, occurred_at, created_at)`
- ids are `bigint GENERATED ALWAYS AS IDENTITY`; `tenant_id` is `text NOT NULL REFERENCES tenants`.

Rules:

1. A contact, opportunity or activity can never reference an account (or an activity a contact) of
   another tenant, even when written by a migration job running as the owner. Use the schema, not a trigger.
2. `stage` is one of `prospecting, qualification, proposal, negotiation, closed_won, closed_lost`;
   `amount >= 0`; a closed stage (won or lost) needs a `close_date`. Activity `type` is one of
   `call, email, meeting, task, note`.
3. A live (not soft-deleted) contact email is unique per tenant, case-insensitively; a soft-deleted
   contact's email can be reused.
4. The legacy Salesforce Id (`sf_id`) is unique per tenant on accounts, contacts and opportunities,
   and may be NULL for records created natively in Keystone.
5. `custom_fields` holds migrated `__c` fields and gets a GIN index.
6. Row-level security on `accounts`, `contacts`, `opportunities`, `activities`: enabled AND forced,
   one policy per table that filters reads and checks writes on
   `tenant_id = current_setting('app.tenant_id', true)`. With no tenant set, `keystone_app` gets zero
   rows (not an error).
7. Role `keystone_app`: `NOLOGIN` (login roles are granted membership), no `BYPASSRLS`, not the table
   owner, with exactly the grants the services need.
8. Indexes so the three `queries/*.sql` do not sequential-scan the big tables when run as
   `keystone_app`. Note the RLS predicate is part of every plan.

## Acceptance criteria (what the grader checks)

- Migrations apply on an empty database and the seed loads.
- RLS: zero rows without a tenant; only own rows with a tenant; inserts and updates into another
  tenant rejected; RLS forced on all four tables; `keystone_app` cannot log in or bypass RLS; it can
  still write its own tenant's rows.
- Constraints: cross-tenant references rejected by foreign keys; stage, amount and close-date rules;
  live-email uniqueness with soft-delete reuse; `sf_id` unique per tenant only; GIN on `custom_fields`.
- Plans (after `ANALYZE`, as `keystone_app`): no `Seq Scan` on `activities`, `opportunities` or
  `accounts` for the three queries.
- `ANSWER.md`: your key decisions, the `make plans` output for each query with one sentence on
  why the planner picked it, and an explanation of what the custom-field plan does with the GIN index
  under RLS (look closely at which index it uses, and find out why).

## How to run

```bash
make setup      # links the shared toolchain (first run installs it once)
make test       # visible tests
make plans      # EXPLAIN (ANALYZE, BUFFERS) for queries/*.sql as keystone_app
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade backend/w2-c1
make clean
```

PGlite is real PostgreSQL 18 compiled to WebAssembly, in one process and one session. Planner, RLS,
constraints and `EXPLAIN` behave as on a server; timings do not.
