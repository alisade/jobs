# ANSWER: awsfde/w2-c1 AgentCore Runtime entrypoint with per-tenant, per-user Memory

## Approach

<!-- Where identity comes from and why the container can trust it; how you structured invoke(). -->

## Fix

<!-- Coding exercise: what you implemented, and anything in the starter you changed. -->

## Trade-offs / what I would do in production

<!-- IAM on the runtime role scoped with bedrock-agentcore:namespace conditions, what happens if
someone removes the JWT authorizer, session id generation on the caller side, memory event expiry,
observability (OTel spans for recall/remember), streaming responses. -->
