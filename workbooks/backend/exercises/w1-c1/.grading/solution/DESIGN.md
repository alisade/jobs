# Design: Keystone platform layer (whiteboard write-up)

## Requirements and non-goals

Functional (what product teams and agents get from the platform):
- Systems of record for accounts, contacts, leads, opportunities (line items, contact roles), activities,
  renewals and partner deal registrations, with owners and custom fields.
- Versioned REST APIs per capability, a read-only GraphQL layer for UI and agent reads that join entities.
- Domain events for every state change (AccountUpdated, LeadConverted, OpportunityStageChanged,
  ActivityLogged, ...) on Kafka, with a schema registry and compatibility rules.
- Workflow primitives on Temporal: assign (round-robin with override), approve (with escalation timers),
  notify, scheduled create (renewal 120 days before contract end), sync (CRM to Keystone during migration).
- An agent tool surface (MCP) with task-level tools, delegated identity and an audit log.
- Tenant onboarding: create a tenant, an app client, quotas and a docs page without a ticket to Keystone.

Non-functional: read APIs 99.9%, writes 99.5% during migration then 99.9%; timeline p95 < 200 ms for 50
items on accounts with 400,000 activities; support console reads p95 < 150 ms; RPO 5 min, RTO 1 h;
audit and activities retained 7 years, append-only audit.

Non-goals for phase 1: reporting and dashboards (the warehouse keeps that job), email sync, a UI
framework for product teams, forecasting, territory planning tools, external customers as tenants.

## Estimates

| Item | Now | In 3 years | Arithmetic |
|---|---|---|---|
| Activities heap | 58 GB | about 105 GB | 48 M x 1.2 KB; +13.2 M/yr (1.1 M x 12) -> 88 M rows |
| Activities with indexes | about 80 GB | about 150 GB | timeline + subject indexes add about 40% |
| Contacts | 3.5 GB | about 5 GB | 2.3 M x 1.5 KB, +12%/yr |
| Accounts / opportunities | 0.8 GB / 1.9 GB | small | |
| Activity writes | 0.42/s average | peak 90/s | 1.1 M / (30 x 86,400 s); Q4 campaign peak from volumes.md |
| Stage changes | about 0.3/s in business hours | | 9,000 / 8 h |
| Reads | 1,800 rps peak | | support console about 1,100 rps, rest about 700 rps |
| Agent tool calls | 150 rps forecast | | bursty, 3-8 calls per turn: treat as 3x burst = 450 rps |

What this decides:
- Only activities are big. Partition activities by month (range on occurred_at, about 1.1 M rows and 1.3
  GB per partition) so 7-year retention and legal hold are partition operations, and keep the timeline on a
  keyset index. Everything else fits in plain tables in one Postgres cluster with room to spare.
- The write path is small (220 rps peak). One primary per region is enough; no sharding in phase 1.
- Reads dominate, and the support console is 60% of them with a 150 ms budget: serve it from a read
  replica with a short cache (60 s TTL, invalidated by events) for account and contact cards.
- Connection budget: at 1,800 rps with about 5 ms of DB time per request, about 9 busy connections
  in steady state (Little's law: 1,800 x 0.005). Pools of 10 per pod, 6 pods per service, behind
  PgBouncer in transaction mode keep the primary under about 150 server connections.

## Core entities and data model

```text
tenant (id, name, region)
user (id, tenant_id, manager_id, roles)                      -- synced from the IdP
account (id uuid, tenant_id, sf_id char(18) null, parent_id, record_type, name, owner_id,
         partner_tier, custom_fields jsonb, version, created_at, updated_at, deleted_at)
contact (id, tenant_id, account_id null, sf_id, email, name, owner_id, custom_fields jsonb, ...)
lead (id, tenant_id, sf_id, status, converted_account_id, converted_contact_id, converted_opportunity_id, ...)
opportunity (id, tenant_id, account_id, sf_id, stage, amount numeric(14,2), close_date, owner_id, version, ...)
opportunity_line_item (id, tenant_id, opportunity_id, product_id, quantity, unit_price, discount_pct)
opportunity_contact_role (tenant_id, opportunity_id, contact_id, role)
activity (id, tenant_id, occurred_at, kind, subject, body, who_lead_id, who_contact_id,
          what_type, what_id, account_id, owner_id, sf_id)      -- partitioned by month on occurred_at
renewal (id, tenant_id, opportunity_id, contract_ref, contract_end)
deal_registration (id, tenant_id, partner_account_id, status, approver_id, ...)
audit_log (id, at, actor, on_behalf_of, app_id, tenant_id, action, args_sha256, outcome, trace_id)
```

- Surrogate UUIDv7 keys (time-ordered, good index locality) plus the legacy 18-character CRM id in an
  indexed `sf_id` column, unique per tenant. 15-character ids are converted to 18 at import.
- `tenant_id` on every tenant table; foreign keys are composite `(tenant_id, x_id)` so a row can never
  point at another tenant's parent.
- Polymorphic WhoId/WhatId: `who` becomes two nullable typed FKs (lead or contact, CHECK exactly one or
  none). `what` stays polymorphic (`what_type`, `what_id`) because it can point at custom objects, but
  every activity also carries a denormalized `account_id` resolved at write time, which is what the
  timeline query needs. Trade-off: no FK on `what_id`; integrity is checked by the activities service.
- Custom fields: 312 fields, 41 of them formulas. Promote the 20-30 fields used in filters to real
  columns; keep the long tail in `custom_fields jsonb` with a GIN `jsonb_path_ops` index; formulas are
  recomputed in code or in projections, not stored as truth.
- Business rules as constraints where the data lives in one row: `CHECK (stage <> 'closed_won' OR
  (amount > 0 AND close_date IS NOT NULL))`, partial unique index on `(tenant_id, lower(email)) WHERE
  deleted_at IS NULL`.

## Service boundaries

```text
                +-------------------- agent gateway (MCP, Python) ----------------+
                |  task tools, delegated identity, audit log, quotas              |
                +------+----------------+-----------------+-----------------------+
                       | REST            | REST            | start workflow
   +-------------------v--+   +----------v---------+   +---v--------------------+
   | accounts-svc (Py)    |   | pipeline-svc (TS)  |   | automation (Temporal)   |
   | accounts, contacts,  |   | opportunities,     |   | assign, approve,        |
   | leads, users mirror  |   | line items, roles, |   | escalate, renewals,     |
   | owns: account,       |   | renewals, deal reg |   | CRM sync                |
   | contact, lead        |   +----------+---------+   +---+---------------------+
   +---------+------------+              |                 |
             | outbox                    | outbox          | activities call APIs
             v                           v                 v
        +--------------------- Kafka (keyed by account_id) --------------------+
        +-------+--------------------------+------------------------+----------+
                v                          v                        v
     activities-svc (Go/Py):      projections: open pipeline,   warehouse sink
     owns activity, timeline      account cards (read models)   (finance feed)
```

- Each service owns its tables in its own schema and database role; no other service has grants on them.
- A service that needs another service's data either calls its API (when it needs the current value
  now) or keeps a read model fed by events (when it needs to join or filter, for example the
  pipeline service keeps an `account_ref (id, name, owner_id, tenant_id)` table).
- Tempting but wrong: a shared "CRM database" that every service reads (that is the current CRM with
  extra steps), and a service per table (contacts and accounts change together and belong to one team).
- A modular monolith for accounts + pipeline is an acceptable phase-1 fallback if the team is small, as
  long as table ownership and the outbox are enforced in code review and CI.

## Interfaces: APIs, events, workflows, agent tools

| Capability | Interface | Why |
|---|---|---|
| CRUD and search on accounts, contacts, opportunities | REST (OpenAPI, /v1) | callers need the result now; standard methods, generated clients |
| Account 360 for UI and agents (account + contacts + open opportunities + recent activity) | GraphQL read layer | joins across owners for reads only; DataLoader per request; no mutations |
| State changes | Events via outbox to Kafka | downstream (projections, warehouse, notifications) must not be coupled to the writer's uptime |
| Lead assignment, discount approval, renewal creation, deal registration approval | Temporal workflows started through an API | long-running, human steps, timers, retries; product teams get a typed start API, not the engine |
| Bulk import, CRM sync | Workflow + batch API | resumable, idempotent, observable |
| Agent actions | MCP tools | task-level (find account, get timeline, log activity, propose assignment), not one tool per endpoint |

API rules: every POST takes an `Idempotency-Key` (agents and workflow activities retry), cursor
pagination on `(created_at, id)` with opaque cursors, RFC 9457 problem details, additive changes only
within a version, deprecation window of two quarters. Event rules: keyed by account id (per-account
ordering), versioned event types, full-state events for entities, thin events for high-volume activities.

## Where the CRM's hidden logic goes

| CRM logic | Keystone home |
|---|---|
| Validation rules on one record (Closed Won needs amount and date) | CHECK constraints plus the same rule in the service for a good error message |
| Discount > 20% needs manager approval | approve workflow; the opportunity stays in "pending approval" until the update arrives |
| Lead assignment flow (round-robin, override) | assign workflow with a manager override update |
| Renewal auto-created 120 days before contract end | scheduled workflow per contract, driven by the billing feed |
| Roll-ups (Account.Open_Pipeline__c) | projection fed by OpportunityStageChanged events, eventually consistent, documented lag |
| Trigger: block deleting accounts with open opportunities | accounts-svc asks the pipeline read model; soft delete only |
| Trigger: copy partner tier down the hierarchy | computed on read from the parent chain (max depth 5), not copied |
| Sharing rules | RLS on tenant_id, plus an explicit partner-manager policy (see below) |
| Formula fields (Days_In_Stage__c) | computed in the API response, not stored |
| Unused flows (inventory shows 19 with no runs in 12 months) | dropped, listed in the cutover notes |

## Multi-tenancy and access

- Shared schema with `tenant_id`, enforced by Postgres RLS (ENABLE and FORCE, app roles without
  BYPASSRLS, `SET LOCAL app.tenant_id` per transaction under PgBouncer transaction mode). See ADR 0001.
- EU residency: the two regulated customers' data cannot sit in the US region. Run a second Keystone
  deployment (same code, its own database and Kafka) in the EU region for `bu-emea`; the platform
  routes by tenant. Confirm with legal whether the whole tenant or two accounts must move; the design
  works either way because tenant is the unit of placement.
- Cross-tenant access (partner managers): an explicit `partner_scope` policy that grants SELECT on
  partner-type accounts to users with the partner-manager role, carried as a second session setting.
  No BYPASSRLS anywhere in application paths.
- Agents: the agent gateway receives the user's delegated token (OAuth token exchange), sets the same
  tenant and user context a user request would, so RLS applies unchanged. Agents never get a broader role.

## Deep dive 1: the activity timeline

- Query: newest 50 activities for one account, then the next page.
  `SELECT ... FROM activity WHERE tenant_id = $1 AND account_id = $2 AND (occurred_at, id) < ($3, $4)
  ORDER BY occurred_at DESC, id DESC LIMIT 50`.
- Index: `(tenant_id, account_id, occurred_at DESC, id DESC)` on each monthly partition. The query reads
  at most a few index pages per partition and stops after 50 rows; the planner walks partitions newest
  first (Merge Append with ordered partitions), so the 400,000-activity account costs the same as a
  small one.
- Writes: 90/s peak is trivial for Postgres; the risk is hot accounts and the GIN index on bodies, so
  full-text search on activity bodies goes to the search index fed by events, not to Postgres.
- Retention and legal hold: detach partitions older than 7 years to cold storage unless the tenant has a
  hold flag; holds are per tenant, so a held tenant's rows are copied out before the detach.
- Failure modes: a missing partition for next month (create 3 months ahead with pg_partman and alert);
  a long-running report on the primary (reports go to a replica or the warehouse).

## Deep dive 2: agent writes

- Tools are task-level: `log_activity`, `propose_lead_assignment`, `draft_renewal`. A tool never
  assigns or discounts directly: it starts the approve or assign workflow and returns a proposal id.
- Every tool call carries an idempotency key; the gateway records (agent id, on-behalf-of user, tenant,
  tool, args hash, outcome, trace id) in the append-only audit log before returning.
- Quotas per agent and per user (token bucket at the gateway), payload size limits, and a kill switch
  per agent app.
- Prompt injection through record content is expected: tool scoping and the delegated identity are the
  control, not instructions in the prompt.

## Migration path off the CRM

1. Phase 0: CDC from the CRM (Change Data Capture events) into Keystone, CRM is source of truth;
   Keystone is read-only for apps; reconciliation report nightly (row counts per object, checksums over
   normalized fields, sampled field diffs, orphan checks).
2. Phase 1 per capability (activities first: high volume, low coupling): the routing layer sends writes
   for that capability to Keystone, Keystone becomes source of truth, a reverse sync keeps the CRM
   updated for apps not yet moved. Rollback: flip routing back, replay Keystone changes to the CRM from
   the outbox.
3. Then contacts and accounts, then pipeline (the most automation), each with its own cutover, a
   reconciliation gate (zero unexplained diffs for 7 days) and a rollback plan.
4. Finance feed: the warehouse sink reads Keystone events from day one, compared against the CRM
   extract until pipeline cuts over.

## Operations

- SLOs per API (availability and latency), per consumer (lag), per workflow (time to approval).
- Traces across API, outbox, Kafka and workflow activities (trace id in event headers).
- Capacity: one primary per region with a synchronous standby (RPO well under 5 min) and async replicas
  for reads; restore tested quarterly against the 1 h RTO.

## Risks and open questions

- Tenant definition (BU, app or both) and multi-tenant users: ask before building the session model.
- EU residency scope: whole tenant or two accounts.
- Account ownership conflicts between sales and partner teams: needs a business owner per field group.
- Agent traffic forecast could be 10x wrong; the gateway quotas and the read replicas are the buffer.
