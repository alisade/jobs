# Reference: awsfde/w2-c1

Reference code: `.grading/solution/ask_runtime/app.py` and `memory.py`.

- **Trust boundary.** AgentCore Runtime with a `customJWTAuthorizer` validates the bearer token before
  the request reaches the container; with `Authorization` on the request header allowlist the token is
  forwarded, so the container decodes its payload. That is only safe because the runtime is the only
  ingress. If someone removes the authorizer, the container would trust unsigned tokens: say so, and
  consider re-verifying against the Cognito JWKS in high-risk deployments.
- **Partitioning.** `actorId = "<tenant>:<sub>"` keeps actors unique across tenants even if two IdPs
  issue the same `sub`. The long-term namespace `/tenant/{tenantid}/actor/{actorId}/preferences/` uses a
  custom namespace variable supplied on each `CreateEvent` (`extractionConfig.namespaceVariables`);
  values must be lowercase, so the tenant claim is validated. Retrieval always uses the resolved,
  normalized namespace (leading and trailing slash), which is also the value IAM conditions
  (`bedrock-agentcore:namespace`) must match.
- **Defense in depth.** Scope the runtime's execution role to `RetrieveMemoryRecords` on
  `/tenant/*` paths and, where you can mint per-tenant credentials, to that tenant's prefix.
- **Ping.** `HealthyBusy` keeps the session alive while work is in flight. `time_of_last_update` moves
  only when the status changes; a timestamp that advances on every ping prevents the idle timeout and
  keeps sessions until max lifetime.
- **Degradation.** Throttled memory should not fail the answer; a missing permission should.
