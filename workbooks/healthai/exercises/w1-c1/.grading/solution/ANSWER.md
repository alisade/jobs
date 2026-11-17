# ANSWER: healthai/w1-c1 PA intake API

## Approach

A `_Base` model carries the shared fields and validators; three category models add their fields and a
`Literal` category, combined into a discriminated union so the error names the category and validation
is O(1). The route only orchestrates: eligibility under `asyncio.timeout`, the clock, the store.

## Fix

- Models: `extra="forbid"`, `AwareDatetime`, ICD-10-CM shape check with normalization, strict ints,
  expedited justification as a model validator.
- Clock: 72 elapsed hours for expedited; 7 days on the plan's wall clock via `zoneinfo` for standard
  (tests cover spring forward, fall back and a sender offset different from the plan zone); QHP on the
  FFEs returns no federal clock.
- 503 on eligibility timeout, idempotency key with body fingerprint (409 on mismatch), lifespan-managed
  client and stores on `app.state`.

## Trade-offs / what I would do in production

Idempotency records in Firestore or Postgres with a TTL, written in the same transaction as the case.
Retry eligibility once with jitter inside the timeout budget, then 503. Pended-for-information handling
and stricter state rules need their own clock rules; keep them in one tested module. Strip input echoes
from 422 bodies because they can contain PHI.
