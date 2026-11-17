# backend/w3-t1 - The partner sync is missing contacts

**Type:** troubleshooting | **Estimate:** 1.5 hours | **Study plan:** Week 3 (Thu: idempotency keys and cursor pagination; Wed: RFC 9457)

## Scenario

Lumenfold's marketing automation pulls every partner-portal contact from Keystone's accounts-svc
(`GET /v1/contacts`) each night. Since the November migration rehearsal its reconciliation keeps
reporting contacts missing, and the 2026-11-16 campaign uses that audience. Marketing Ops opened
KEY-2291 and thinks your rate limiter is eating pages. Marcus Oyelaran (on call) attached the service
side of the evidence and handed it to you.

## What you have

| Path | What it is |
|---|---|
| `incident/TICKET.md` | the ticket (created by `make setup`) |
| `incident/partner-sync.log` | the partner's sync client log for the failing run |
| `incident/accounts-svc-access.jsonl` | the service access log for the same run, cursors decoded |
| `incident/replica-queries.txt` | counts the on-call engineer ran on the replica |
| `contacts_api/` | the service code: `main.py` (route), `pagination.py`, `db.py` (schema), `seed.py` |
| `scripts/walk.py` | `make repro`: walks your code over the same data the partner has |
| `tests/`, `conftest.py`, `testkit.py` | visible tests and their fixtures |

The service runs on SQLite (aiosqlite) here; the behavior is the same on PostgreSQL.

## Your task

1. Find the root cause. Back it with evidence from the bundle and from `make repro`.
2. Fix the pagination so a full walk returns every contact exactly once, including while new
   contacts are being inserted. Keep the response shape (`data`, `next_cursor`).
3. A cursor the service did not issue must get a 400 `application/problem+json` (RFC 9457), not a
   500 and not a silently wrong page. `limit` defaults to 50, is capped at 200, and `limit < 1` is a 400.
4. Make the index in `db.py` match the sort you now use.
5. Fill in `ANSWER.md`: root cause with evidence, why the partner's theory does not explain it, the
   fix and how you verified it, and what you would tell the partner.

## Acceptance criteria (what the grader checks)

- Every row exactly once over full walks with many identical `created_at` values, at several page sizes.
- No skips or duplicates when rows are inserted during the walk.
- Opaque URL-safe cursor; tampered or foreign cursors return a 400 problem.
- Page size bounds as above; tenant isolation unchanged.
- An index on `(tenant_id, created_at, id)`.
- `ANSWER.md` root cause and evidence (most of the points).

## How to run

```bash
make setup      # venv + incident bundle
make repro      # pages=... received=... missing=...
make test       # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade backend/w3-t1
make clean
```
