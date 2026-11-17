# ANSWER: awsfde/w2-c1 AgentCore Runtime entrypoint with per-tenant, per-user Memory

## Approach

Identity comes from the bearer token that the runtime's customJWTAuthorizer already validated and
forwarded (Authorization is allowlisted). invoke() checks token, claims, session header and prompt in
that order before touching Memory, then recall -> model -> remember inside an in-flight counter.

## Fix

memory.py: actor_id "<tenant>:<sub>", normalized namespace, RetrieveMemoryRecords in that namespace,
CreateEvent with USER/ASSISTANT turns and namespaceVariables {"tenantid": tenant}. app.py: status
codes, ignored payload identity fields logged, degradation on ThrottledException, 500 on other
Memory errors, ping with a lock-protected status and change time.

## Trade-offs / what I would do in production

Runtime role scoped with bedrock-agentcore:namespace conditions; event expiry set to the retention
the customer signed; OTel spans around recall and remember in AgentCore Observability; session ids
minted by the web tier (33+ chars) per conversation; SSE streaming for long answers.
