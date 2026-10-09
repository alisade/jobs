# Reference: fde/w4-t1 gateway identity bleed

## Root cause

PR #388 moved the bound principal from `request.state` into a module-level dict in
`gateway/identity.py`. One process serves every request on one event loop, so that dict
is a single slot shared by every request in flight.

`AuthMiddleware` binds the principal, then `await self.limiter.hit(principal)` (a Redis
round trip, ~12 ms). That await is a suspension point: other requests run their
middleware and overwrite the slot. When the first request resumes, `call_tool` reads
`identity.current_principal()` and gets whoever bound last. It reads it twice (before
`sessions.load` and again for the audit line), so even the audit log disagrees with
itself: `customer=<X> session=gw-<Y>`. `release()` is a no-op, so the last principal also
lingers after its request.

Why one test account never reproduces: with a single customer every overwrite writes the
same value. It needs two customers with overlapping requests, which the 19:00 push makes
common.

## The red herrings

- TTL 60 -> 900 s: `SessionStore` caches by principal, and the record's session id is
  derived from that principal. A longer TTL can only serve A's own record to A. Setting
  `SESSION_CACHE_TTL_S=0` and re-probing still leaks.
- `httpx connection pool full`: an unrelated client pool to the CDN; no effect on identity.
- Provenance holds in the audit log are a symptom: A's lookup landed in B's executor, so
  A's add (run as A) finds no provenance.

## Fix (one file)

```python
_principal: ContextVar[str | None] = ContextVar("gateway_principal", default=None)

def bind(principal): return _principal.set(principal)
def release(handle): _principal.reset(handle)
def current_principal():
    p = _principal.get()
    if p is None: raise Unauthenticated(...)
    return p
```

Each ASGI request runs in its own task (uvicorn/httpx create one per request), and a task
runs in a copy of the context taken when it was created, so a `set` in one request is
invisible to the others. `reset(token)` in the middleware's `finally` restores the
previous value. Passing the principal explicitly (request.state / scope) is equally
correct; a global lock is not (it serializes every request behind Redis).

## Verify

`make test`; `make clean && make setup && make probe` -> 0 mismatches, 0 leaks.

## Production

- A concurrency test (many customers, gathered) in CI; this bug passes every
  single-request test.
- Review rule: no module-level mutable state that is per-request; ContextVar or explicit.
- Remediation: carts written during the window may hold foreign lines; clear or notify
  affected sessions (audit lines with customer != session digest identify them).
- Ship the one-file fix; do not revert the release (the TTL and rate limiter are fine).
