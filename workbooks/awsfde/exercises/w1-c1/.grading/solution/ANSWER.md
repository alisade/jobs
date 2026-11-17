# ANSWER: awsfde/w1-c1 Converse tool-use loop

## Approach

`build_request()` is a pure function so every request is testable. `run_turn()` keeps one
`messages` list and branches only on `stopReason`. Tool calls go through `_run_tool()`, which
checks the tool exists, validates the input against the tool's JSON schema, then calls the handler
with the verified `CallerContext`. Every failure becomes a `toolResult` with `status: "error"`.

## Fix

Implemented `build_request`, `run_turn`, `_run_tool`, `Usage.add` and `estimate_cost_usd`. Results
for parallel `toolUse` blocks are returned in one user message in the original order. A
`tenant_id` in tool input is logged as `ignored_tenant_arg` and rejected by the schema.

## Trade-offs / what I would do in production

- ConverseStream for time to first token in the chat UI.
- One retry layer (botocore standard or adaptive mode, small max_attempts) for ThrottlingException
  with backoff and jitter; never stack app retries on top of SDK retries.
- A cachePoint after the static system prompt and tool specs to cut input cost on multi-round turns.
- Model invocation logging to S3 and CloudWatch Logs, requestMetadata with tenant and request id
  for per-tenant cost attribution, and alarms on InvocationThrottles.
- Guardrail: denied topics (legal advice), PII masking of email and phone, and a contextual
  grounding check once answers come from a Knowledge Base.
