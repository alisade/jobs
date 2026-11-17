# awsfde/w2-c1 - AgentCore Runtime entrypoint with per-tenant, per-user Memory

**Type:** coding | **Estimate:** 2-2.5 hours | **Study plan:** Week 2 (Mon: Runtime; Wed: Memory; Thu: Identity)

## Scenario

Tidewater Analytics (fictional) is moving the Tidewater Ask agent from a Lambda to **Amazon Bedrock
AgentCore Runtime** so sessions get their own microVM and the agent can keep per-user memory. The
runtime is configured with the HTTP protocol and a `customJWTAuthorizer` that points at the Cognito
user pool, and `Authorization` is on the runtime's request header allowlist, so the container
receives the caller's already-validated bearer token.

The customer's security architect signed off on one design point and wants to see it in code:
**memory is partitioned by tenant and by user, and the partition comes from the verified token,
never from the request body.** Last quarter a competitor's assistant leaked one user's saved
preferences to another; the architect wants a test that proves user B cannot recall user A's facts.

Memory design (in `config.json`): one AgentCore Memory with a user preference strategy whose
namespace template is `/tenant/{tenantid}/actor/{actorId}/preferences/`, where `{tenantid}` is a
custom namespace variable supplied on every `CreateEvent` and `actorId` is `<tenant_id>:<sub>`.

## What you have

| Path | What it is |
|---|---|
| `config.json` | memory id, strategy and namespace template, runtime settings |
| `ask_runtime/identity.py` | case-insensitive header lookup and `bearer_claims()` for the validated token (done; read the docstring) |
| `ask_runtime/model.py` | a stub model call (done) |
| `ask_runtime/memory.py` | `actor_id`, `namespace`, `recall`, `remember` - **your work** |
| `ask_runtime/app.py` | `AgentApp.ping()` and `AgentApp.invoke()` - **your work**; `make_server()` (the HTTP wiring) is done |
| `tests/` | visible tests: a real `bedrock-agentcore` client with a botocore `Stubber` |

botocore validates every Memory request against the real `bedrock-agentcore` service model
(for example the `actorId` and `sessionId` patterns), so a malformed request fails the tests the way
it would fail with a `ValidationException`. Nothing calls AWS.

## Your task

1. `memory.py`
   - `actor_id(claims)` -> `"<tenant_id>:<sub>"`. Raise `IdentityError` when `tenant_id` or `sub` is
     missing, or `tenant_id` is not lowercase `^[a-z0-9][a-z0-9-]{1,39}$` (custom namespace values
     must be lowercase).
   - `namespace(claims)` -> the resolved namespace, normalized with one leading and one trailing slash.
   - `recall()` -> `RetrieveMemoryRecords` in that namespace only (`searchCriteria.searchQuery`,
     `topK`); return the record texts.
   - `remember()` -> one `CreateEvent` with the USER and ASSISTANT turns as `conversational`
     payload items, the caller's `actorId` and `sessionId`, an `eventTimestamp`, and
     `extractionConfig.namespaceVariables = {"tenantid": <tenant_id>}`.
2. `AgentApp.invoke(headers, body)` (`POST /invocations`):
   - no bearer token: 401; claims without a valid tenant or subject: 403; no
     `X-Amzn-Bedrock-AgentCore-Runtime-Session-Id` header: 400; no non-empty `prompt` in the JSON
     body: 400. None of these touch Memory. Header names are case-insensitive.
   - Tenant, actor and session come only from the claims and the header. Fields such as `actor_id`,
     `tenant_id` or `session_id` in the payload are ignored (log them as an event).
   - recall, then the model, then remember. Response:
     `{"response", "status": "success", "memory": "used" | "degraded", "session_id"}`.
   - `ThrottledException` (or `ServiceException`, `RetryableConflictException`) from Memory degrades:
     answer without memory, `memory: "degraded"`, log a `memory_degraded` event. Any other Memory
     error (for example `AccessDeniedException`) is a 500: a broken role must be loud.
3. `AgentApp.ping()` (`GET /ping`): `{"status": "HealthyBusy"}` while any invocation is in flight,
   else `"Healthy"`, with `time_of_last_update` = unix seconds of the last **status change**. Read the
   HTTP protocol contract on why it must not advance on every ping.
4. Fill in `ANSWER.md`.

## Acceptance criteria (what the grader checks)

- Every Memory request passes botocore validation; namespaces and actor ids come only from claims.
- User B's request retrieves only from user B's namespace; payload identity fields change nothing.
- Status codes for missing token, bad claims, missing session, missing prompt.
- Degradation on throttling, a 500 on access denied; ping busy/idle and `time_of_last_update` semantics.
- The real HTTP server (`make_server`) answers `/ping` and `/invocations` on 127.0.0.1.
- `ANSWER.md` explains the trust boundary and what you would add in production.

## How to run

```bash
make setup
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade awsfde/w2-c1
make clean
```
