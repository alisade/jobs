# Reference: healthai/w1-c1

See `.grading/solution/intake/`. Points worth discussing after grading:
- `AwareDatetime` makes naive timestamps a validation error, which is what you want for a regulatory
  clock. `StrictInt` stops "56" from silently becoming 56.
- The two clocks differ on purpose: 72 hours is elapsed time; "7 calendar days" is read here as the same
  wall-clock time in the plan's zone, so across spring-forward the deadline is 167 elapsed hours. State
  the interpretation in the design doc and have compliance sign it off; that conversation is the senior
  signal, not the arithmetic.
- Idempotency: key -> (body hash, case id). In production store it with a TTL in the same transaction
  as the case insert, or two concurrent retries create two cases.
- `asyncio.timeout` around the eligibility call turns a slow dependency into a fast 503 that the caller
  can retry; without it a Cloud Run instance holds requests until the platform timeout.
- Lifespan on `app.state` keeps tests isolated and gives a place to close pooled clients on SIGTERM.
