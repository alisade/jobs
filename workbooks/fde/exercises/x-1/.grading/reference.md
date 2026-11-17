# Reference: fde/x-1 Halyard risk-API client

Full code: `.grading/solution/risk_client/{breaker,client}.py`.

## Token: double-checked single flight

```python
async def _get_token(self) -> str:
    if self._valid(self._token):
        return self._token.value
    async with self._token_lock:
        if self._valid(self._token):      # someone else fetched while we waited
            return self._token.value
        self._token = await self._fetch_token()
        return self._token.value
```

`refresh_at = clock() + expires_in - skew`. On 401, `_invalidate(used)` drops the token only
if it is still the one this call used: another coroutine may already have replaced it, and
dropping the fresh one would cause a second fetch.

## assess: breaker outside, budget around everything

```python
self._breaker.before_call()                 # CircuitOpen: no network
try:
    async with asyncio.timeout(self._budget):
        body = await self._call(payload)    # token + POST + one 401 retry
except TimeoutError:
    self._breaker.record_failure(); raise RiskTimeout(...) from None
except RiskUnavailable:
    self._breaker.record_failure(); raise
except RiskError:
    self._breaker.record_success(); raise   # API is up; our request was wrong
finally:
    self._breaker.release()                 # cancelled trial: free the slot
self._breaker.record_success()
return body
```

Cancellation: an outer `task.cancel()` raises `CancelledError` at whatever await is active
(the lock, the token POST, the assess POST). `asyncio.timeout` only converts *its own*
cancellation to `TimeoutError`; an outer cancel passes through as `CancelledError`, none of
the `except Exception`-family clauses see it, and `finally` releases the half-open slot.

## Breaker

State is derived from `opened_at` and the clock (no timers). Half-open admission sets
`_trial_in_flight` with no await between check and set, so it is atomic on one event loop.
A failure while `opened_at` is set (the failed trial) re-opens with a fresh cool-down.

## Production notes

- Breaker state is per process. With 8 uvicorn workers a dead API costs 8 x threshold calls
  before everything is open; acceptable, and simpler than shared state (Redis) on the hot path.
- Consecutive-failure tripping is fragile at low traffic and slow at high traffic; a rolling
  error-rate window with a minimum request count is the usual upgrade.
- Refresh tokens in the background at ~80% of lifetime so no request ever pays for a fetch.
- Emit: breaker state transitions, budget exhaustion count, token fetch latency, 401 rate.
- The 401 retry is the only retry: inside a 150 ms budget a backoff retry is pointless.
