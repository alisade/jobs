# fde/x-1 - Halyard risk-API client: token cache, latency budget, circuit breaker

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 5 add-on (Wed: advanced asyncio, Thu: exceptions to structured results, Fri: pytest depth), Week 2 Thu (client credentials + latency budgets)

## Scenario

The `AgentTrustMixin` (w3-c1) talks to a `RiskClient` protocol. This is the real client
behind it, for Halyard Risk's API, and it sits in the hot path of every cart write: the
mixin gives it 150 ms. Last quarter a different vendor integration at Northwind took the
storefront down for 40 minutes: its token cache was not single-flight, so when the token
expired at peak, 3,000 coroutines hit the IdP at once, the IdP rate-limited, every call
retried with backoff past its budget, and the event loop drowned in waiters.

The platform team's review checklist for any in-path client is now: one token request per
expiry, early refresh, a hard per-call budget that includes the token fetch and any retry,
no httpx exception crossing the module boundary, and a circuit breaker so a dead dependency
costs ~0 ms instead of the full budget.

## What you build

Edit `risk_client/breaker.py` and `risk_client/client.py` (the TODOs). `errors.py` is given.

### CircuitBreaker (consecutive failures, single half-open trial, injected clock)

| State | `before_call()` | `record_success()` | `record_failure()` |
|---|---|---|---|
| closed | admit | reset the consecutive count | count; at `failure_threshold` -> open (cool-down starts) |
| open (cool-down running) | raise `CircuitOpen` | - | - |
| half_open (cool-down elapsed) | admit ONE trial; others raise `CircuitOpen` until it reports | -> closed, count 0 | -> open, fresh cool-down |

`release()` frees a trial slot without a verdict (the trial was cancelled). `state` is
computed from the clock: no background timers. Constructor validates `failure_threshold >= 1`
and `reset_timeout_s > 0` (`ValueError`).

### HalyardRiskClient.assess(payload) -> dict

- **Token** (RFC 6749 sec. 4.4): `POST token_url`, form `grant_type=client_credentials`,
  `scope=risk.assess`, HTTP Basic `client_id:client_secret` (never the secret in the body).
  Response `{"access_token", "expires_in"}`. Reuse until `expires_in - token_skew_s` has
  elapsed on `clock`. **Single flight**: 50 concurrent callers with no token cause exactly one
  token request.
- **Assess**: `POST {base_url}/v1/assess`, JSON body, `Authorization: Bearer <token>`.
  200 with a JSON object -> return it.
- **Budget**: one `asyncio.timeout(budget_s)` around everything one call does (token fetch,
  assess, the 401 retry). Out of budget -> `RiskTimeout`.
- **401**: drop the token you used, fetch a fresh one, retry once. A second 401 ->
  `RiskUnavailable`. No third attempt, and no retry for anything else.
- **Mapping**: 5xx, 429, transport errors, non-JSON or non-object bodies, token-endpoint
  failures -> `RiskUnavailable`. Any other 4xx -> `RiskError` (not unavailable).
  No `httpx` exception escapes.
- **Breaker**: checked first (open -> `CircuitOpen`, no network call). `RiskUnavailable` and
  `RiskTimeout` are failures; a 200 and a plain `RiskError` are successes (the API is up). A
  cancelled call releases a half-open trial.

## Acceptance criteria

- One token request per token lifetime, refreshed `token_skew_s` early; single flight under
  concurrency.
- Budget holds end to end, including token fetch and the 401 retry.
- Typed errors only; `RiskError` vs `RiskUnavailable` distinction preserved.
- Breaker state machine exactly as the table (a property test compares it against a model).
- Half-open admits exactly one trial under concurrency; cancellation never wedges it.

## How to run

```bash
make setup     # builds/reuses the shared venv fde/.venv
make test      # visible tests (respx-mocked; no network)
# from workbooks/: /grade fde/x-1
make clean
```

Materials: `asyncio.timeout`, `asyncio.Lock`, respx (`side_effect` can be an async
function returning an `httpx.Response`), Hypothesis `@given`.

## What to submit

`risk_client/breaker.py`, `risk_client/client.py`, and `ANSWER.md`. In ANSWER.md say where
cancellation can arrive inside `assess` and what each of your `except` clauses sees then.
