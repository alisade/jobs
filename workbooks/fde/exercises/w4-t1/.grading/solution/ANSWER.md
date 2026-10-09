# ANSWER: fde/w4-t1 Gateway identity bleed

## Approach

Reproduced with `make setup && make probe`: 80 of 100 responses acted for the wrong
customer and one customer's cart held all five products. A single customer by hand never
reproduces it, so I looked for per-process shared state touched on both sides of an
await. Checked the TTL theory first because Platform raised it, then read the request path
middleware -> handler.

## Root cause

`gateway/identity.py` (PR #388) keeps the principal in a module-level dict `_current`:
one slot per process, shared by every concurrent request. `AuthMiddleware.__call__` binds
the principal and then awaits `self.limiter.hit(...)` (Redis round trip). While suspended,
other requests bind their principal into the same slot. On resume, `call_tool` reads
`identity.current_principal()` and gets the last binder, loads that customer's session and
executor, and runs the tool there. `release()` does nothing, so the principal also
survives the request.

Evidence:

```
$ make probe
  LEAK cust-eli-54d53c    expected only AR-1006; cart holds ['AR-1001', 'AR-1003', 'AR-1004', 'AR-1005', 'AR-1006']
responses acting for the wrong customer: 80
$ grep audit run/gateway.log | head
... tool=get_product_details customer=c27d5e8a1f03 session=gw-91be33d07c4a ...
```

The audit line reads the principal twice (once before `sessions.load`, once after) and
the two disagree within one request: the slot changed across the await.

The TTL change is not it: `SessionStore` is keyed by principal and the session id is
derived from the principal, so a longer TTL can only return a customer's own record.
With `SESSION_CACHE_TTL_S=0` the probe still leaks. The httpx pool warning is a CDN client
and unrelated; the provenance holds are a symptom (a lookup landed in another session).

## Fix

`gateway/identity.py`: the principal is a `ContextVar`; `bind` returns the `Token` from
`set`, `release` calls `reset(token)` (the middleware already calls it in `finally`).
Each request runs in its own task with its own context copy, so binds cannot cross.
Verified: `make test` green; `make clean && make setup && make probe` reports 0 wrong
responses and 0 leaks.

## Trade-offs / what I would do in production

- Add the concurrent multi-customer test to CI; single-request tests can never catch this.
- Ban module-level per-request state in review; ContextVar or explicit passing only.
- Identify affected sessions from audit lines where customer digest != session digest and
  clear their carts; notify the three customers.
- Keep release 2026.10.07 (TTL and rate limiter are fine); ship the one-file fix.
