# backend/w4-c1 - Opportunity stage transitions with an outbox (Fastify + Kysely)

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 4 (Mon: event loop and graceful shutdown; Tue: Fastify schemas and Zod; Wed: Kysely, transactions, FOR UPDATE, SET LOCAL)

## Scenario

pipeline-svc owns Keystone's opportunities. Moving a deal between stages is the most important write
in the sales pipeline: sales ops reports on stage history, the forecast consumes the
`OpportunityStageChanged` events, and the Keystone agent assistant will call this endpoint through a
tool (with retries). The first cut ported from the CRM works in the demo and nowhere else: it reads
and writes outside a transaction, ignores the tenant, accepts any stage, loses concurrent updates,
publishes events for changes that never committed, returns ad-hoc error bodies and dies mid-request
when Kubernetes rolls a pod.

## What you have

| Path | What it is |
|---|---|
| `src/transitions.ts` | the route to rewrite (starter: the CRM port) |
| `src/app.ts` | Fastify app factory; add the error handling and readiness here |
| `src/shutdown.ts` | SIGTERM handling to implement |
| `src/db.ts` | PGlite + Kysely setup and `withTenant()` (one transaction as `pipeline_app` with the tenant set locally) |
| `src/problems.ts` | `ProblemError` and `sendProblem()` (RFC 9457) |
| `migrations/0001_pipeline.sql` | opportunities, stage_history, outbox, role and RLS (given) |
| `tests/` | visible tests and helpers (fastify.inject against an in-process PostgreSQL 18) |

## Requirements

`POST /v1/opportunities/:id/transitions` with header `X-Tenant-Id` (and optional `X-User-Id`) and body
`{ "to_stage": "...", "expected_version": 3, "close_date": "2026-11-30" }` (close_date optional).

1. Validate with Zod: `to_stage` one of the six stages, `expected_version` a positive integer,
   `close_date` `YYYY-MM-DD`, no unknown fields. Missing tenant, bad id, bad body or malformed JSON:
   `400`.
2. One transaction (`withTenant`) that: locks the opportunity with `SELECT ... FOR UPDATE`; returns
   `404` when it does not exist or belongs to another tenant (RLS makes these the same); `409` with
   `current_version` when `expected_version` is stale; `422` for a transition not in `ALLOWED`
   (closed stages are terminal); `422` for `closed_won` without `amount > 0` and a close date (body or
   existing). `closed_lost` without a date closes today.
3. On success, in the same transaction: update stage, `version + 1` (and close_date when set), insert a
   `stage_history` row, insert an `outbox` row: `event_id` (uuid), `tenant_id`, `aggregate_type`
   `opportunity`, `aggregate_id` the id as text, `type` `OpportunityStageChanged`, `payload` with
   `event_id, opportunity_id, account_id, from_stage, to_stage, version, changed_by`. Return
   `200 { id, stage, version, close_date, event_id }`.
4. If anything fails before commit nothing is written: no outbox row for a change that did not happen.
   Unexpected errors are `500` problems that do not leak internals.
5. Every error is `application/problem+json` per RFC 9457: `type` (URI), `title`, `status`, `detail`,
   `instance`, plus extension members (`errors`, `current_version`, `allowed`).
6. Graceful shutdown (`installGracefulShutdown`): on SIGTERM, `/readyz` returns `503`, new requests get a
   `503` problem, in-flight requests finish, then the app closes and `exit(0)` is called; `exit(1)` if
   draining exceeds `timeoutMs`. The tests install it before the app boots.

## Acceptance criteria (what the grader checks)

- Happy path writes opportunity, history and outbox consistently; payload fields as specified.
- 400 / 404 / 409 / 422 / 500 as specified, all problem+json; tenant isolation via RLS.
- A failure before commit leaves no outbox, history or version change; two concurrent transitions with
  the same version give one 200 and one 409 and exactly one outbox row.
- The opportunity is read `FOR UPDATE`; `app.tenant_id` does not outlive the transaction.
- Graceful shutdown drains in-flight work before exiting.
- `ANSWER.md`: why the outbox row must share the transaction, `FOR UPDATE` vs optimistic version
  checks, and how this endpoint behaves when an agent retries it.

## How to run

```bash
make setup      # links the shared toolchain
make test       # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade backend/w4-c1
make clean
```

Note: PGlite is one session, so the Kysely driver queues transactions one at a time; row locks cannot
block each other here. The concurrency test still proves the version check, and `FOR UPDATE` is what
makes the same code correct on a real pool.
