# Rubric: awsfde/w1-c1 Converse tool-use loop with a guardrail, tenant-safe tools and cost logging
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Loop correctness and message handling | 15 | Full: assistant message appended verbatim, all toolUse blocks answered in one user message in order, clear stop conditions per stopReason, round limit counted as tool rounds. Partial: works but order/limit semantics implicit or fragile (e.g. assumes one toolUse per message). Zero: loop restarts the conversation or drops messages. |
| 3 | Tenant safety and error handling | 15 | Full: handlers only ever see ctx for tenant; schema validation before the handler; ToolError vs unexpected exceptions separated, unexpected ones logged server-side with a generic message to the model; ignored_tenant_arg logged. Partial: tenant safe but errors raise or leak stack traces. Zero: any path reads tenant from tool input. |
| 4 | Observability and cost | 10 | Full: one structured JSON line per call with request/tenant correlation, cache tokens priced separately, unknown model fails loudly. Partial: totals only, or print instead of logger. |
| 5 | ANSWER.md production thinking | 10 | Full: concrete and correct about at least three of: ConverseStream, retries/throttling with backoff and jitter (and not stacking retry layers), cachePoint for the static system/tools prefix, model invocation logging to S3/CloudWatch, guardrail policy choice (denied topics, PII masking, contextual grounding for RAG answers), per-tenant cost attribution via requestMetadata or logs. Partial: generic. |
Total: 100
