# edgefde/x-1 - CMMS work-order client: retries, Retry-After and idempotency keys (optional)

**Type:** coding | **Estimate:** 2 hours | **Study plan:** Week 7 add-on (Mon-Tue: API integrations: timeouts, retries, idempotency, auth, pagination)

## Scenario

When the Dunmore pump-health model confirms an anomaly, the edge kit raises a draft work order in
Corvane Industrial's CMMS (fictional), which lands in the maintenance planner's queue. The prototype
did one POST with no retry. On the plant network that means two failure modes the planner has already
seen: work orders that never arrive (a 503 during the CMMS's nightly sync), and duplicate work orders
(the CMMS created the order, the response was lost, someone pressed "retry"). The planner's rule:
one anomaly, one work order, always.

The CMMS API (`cmms/fake.py`, complete, read the docstring) supports OAuth client credentials with a
300-second token, an `Idempotency-Key` header on `POST /api/v2/work-orders` (a repeated key returns
the same order), and paginated listing. A fake transport injects 500/503/429 (with `Retry-After` in
seconds or as an HTTP date), connect timeouts and "commit then timeout" faults. Time is a fake clock,
so backoff is instant and measurable.

## What you have

| Path | What it is |
|---|---|
| `cmms/client.py` | the client you implement (the prototype's draft is there) |
| `cmms/fake.py` | fake CMMS, fake clock and fault-injecting transport (do not edit) |
| `scripts/demo.py` | `make demo`: one work order through 503, a lost response and a 429 |

## Your task (the contract)

- `CMMSClient.idempotency_key(machine, alert_window_start)`: deterministic, different per machine and
  per window, so the same anomaly gives the same key across retries, restarts and gateways.
- Every request goes through one retry loop and passes `timeout=self.timeout` to the transport.
- Retry only 429, 500, 502, 503, 504 and `TransportTimeout`. Anything else >= 400 raises
  `PermanentError(status, body)` immediately (no retry on 400/404/409/422).
- Backoff: full jitter, `sleep(rng.uniform(0, min(max_delay, base_delay * 2 ** attempt)))` for retry
  number `attempt` = 1, 2, ...; when the response has `Retry-After` (seconds or an HTTP date), sleep
  exactly that instead.
- Retry budget: never more than `max_attempts` attempts; if the next wait would push the total sleep
  past `retry_budget_s`, raise `RetryBudgetExceeded` without sleeping.
- Auth: get a token with client credentials, cache it, refresh it when it is within 30 s of expiry,
  and on a 401 refresh once and retry (the refresh does not count as an attempt).
- `raise_work_order(machine, alert_window_start, title, priority)` sends the key and returns a
  Pydantic `WorkOrder`; `list_work_orders(asset_id)` follows `next_page_token` to the end.

## Acceptance criteria (what the grader checks)

- 40 anomalies through a link with 30% faults of every kind create exactly 40 work orders.
- One key per anomaly on every retry and after a client restart.
- `Retry-After` honoured in both formats; jitter within the full-jitter bounds; no retry on 422;
  budget exhaustion raises clearly and creates nothing; a `Retry-After` beyond the budget fails fast.
- Timeout on every call; token cached, refreshed on expiry and after a 401; pagination complete.
- `ANSWER.md`: why the idempotency key, not the retry loop, is what prevents duplicates.

## How to run

```bash
make setup && make demo && make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade edgefde/x-1
make clean
```

## What to submit

`cmms/client.py` and a filled-in `ANSWER.md`.
