# Reference: connect/w7-c1

Reference code: `.grading/solution/src/servicenow.ts` and `src/handler.ts`.

What an interviewer looks for:

- **One deadline.** The handler computes `deadline = start + 6500 ms` and passes it everywhere.
  Connect's synchronous invoke limit is 8 s and Connect itself retries a failed invoke inside that
  window, so the Lambda must finish well inside it and answer with a routable result rather than an
  error. `checkBudget` before each call; a `Retry-After` longer than the remaining budget is a
  `BudgetExceeded`, not a sleep.
- **Token cache at module scope** with a 60 s skew, cleared and refreshed once on 401 (revoked or
  rotated token), credentials in the form body (`client_credentials` grant).
- **Pagination by `Link rel="next"`** (or `X-Total-Count` + offsets). Reading only the first page
  made the count wrong AND broke the idempotency guard.
- **Idempotency.** `correlation_id = ContactId` plus lookup-before-create handles Connect and client
  retries. It still races if two invokes run concurrently; the robust fix is a conditional write
  (DynamoDB `attribute_not_exists(contactId)`) before calling ServiceNow, or a ServiceNow scripted
  REST API that upserts on correlation_id server-side. See x-1 for the production incident.
- **Flat STRING_MAP always.** `DEGRADED` with a `reason` lets the flow say "I could not reach the
  ticketing system, an agent will help you" and set a contact attribute for the screen pop.
- **Encoded-query hygiene.** `^` adds clauses (`^OR`, `^NQ`); strip or reject it in values.
- Production: secret in Secrets Manager with the Lambda extension cache, structured logs keyed by
  ContactId without PII, a CloudWatch metric on DEGRADED, and consider moving incident creation to
  an EventBridge-driven after-contact step when the IVR does not need the number.
