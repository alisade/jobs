# backend/w3-c1 - Idempotency keys that survive concurrent retries

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 3 (Thu: idempotency keys; Tue: async SQLAlchemy sessions; Wed: RFC 9457)

## Scenario

Keystone's accounts-svc is called by other teams' services, by Temporal activities and by agents. All
of them retry on timeouts and 5xx, so every POST takes an `Idempotency-Key`. The first implementation
(`app/idempotency.py`) reads the key table, runs the handler if nothing is there, then writes the
result. In Priya Natarajan's load test, a workflow activity that timed out was retried 20 times in
parallel by the worker pool, and accounts-svc created several identical accounts for one request. The
directory enrichment call inside the handler (`app/directory.py`, about 20 ms, sometimes failing) makes
the window wide. Fix the design, not just the race in the test.

## What you have

| Path | What it is |
|---|---|
| `app/main.py` | FastAPI app: `POST /v1/accounts`, `GET /v1/accounts/{id}`, `POST /v1/accounts/{id}/contacts` |
| `app/idempotency.py` | `run_idempotent(request, tenant_id, handler)`: the part you rewrite |
| `app/models.py` | SQLAlchemy 2 models, including `IdempotencyKey` with primary key `(tenant_id, key)` |
| `app/db.py` | aiosqlite engine (WAL, busy timeout), session factory |
| `app/problems.py` | RFC 9457 helpers: `ProblemError`, `problem()` |
| `app/directory.py` | fake enrichment dependency with latency, failure injection and a gate for tests |
| `conftest.py`, `testkit.py`, `tests/` | fixtures and visible tests |

SQLite stands in for Postgres. The pattern is the same: the database's unique constraint is the only
thing that arbitrates concurrent claims.

## Requirements

1. `Idempotency-Key` is required on every POST: missing -> 400 problem; longer than 255 characters -> 400.
2. Keys are scoped per tenant (`X-Tenant-Id`): the same key in two tenants is two different requests.
3. Claim the key by INSERTing a row (status `in_progress`) under the `(tenant_id, key)` primary key.
   Do not check-then-insert. Exactly one concurrent request may run the handler.
4. Store a request fingerprint: method, path and a canonical form of the JSON body (key order and
   whitespace do not matter).
5. On a later request with the same key:
   - different fingerprint -> 422 problem;
   - still `in_progress` -> 409 problem with a `Retry-After` header;
   - completed -> the stored status and body, plus header `Idempotent-Replayed: true`. Stored 4xx
     outcomes (for example a 404) are replayed too; error bodies keep `application/problem+json`.
6. If the handler raises or returns a 5xx, release the key so a retry can run. The client sees a 500
   problem (already handled by `problems.install`).
7. Keys expire after 24 hours (use `request.app.state.clock()`): an expired key is treated as new and
   the old row is replaced, not duplicated.

## Acceptance criteria (what the grader checks)

- Concurrency: 20 identical requests in parallel create exactly one account; every response is a 201
  with the same id or a 409 problem with `Retry-After`; a later retry replays.
- An in-flight duplicate (the first request held at the directory call) gets 409.
- Fingerprint mismatch and same key on another path -> 422; canonical body comparison.
- Failure releases the key; per-tenant scoping; expiry; contacts endpoint has the same guarantees.
- `ANSWER.md` explains the design and its production trade-offs.

## How to run

```bash
make setup
make test        # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade backend/w3-c1
make clean
```
