# Rubric: connect/w6-c2 After-contact summarization pipeline
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Safety and data protection | 15 | Full: redaction before the model and on the output, untrusted-data system prompt, guardrail with trace, guardrail/invalid outputs never written, no transcript or PII in logs (log entity types and token counts, not text), ANSWER.md mentions model invocation logging retention and who can read it. Partial: one layer only. |
| 3 | Reliability | 15 | Full: claim before work, release on retryable failure, complete only after all writes, DUPLICATE without side effects, IN_PROGRESS retried, Bedrock/ServiceNow failures classified as retryable, KB best effort. Partial: idempotency but wrong ordering (complete before writes) or claims never released. |
| 4 | Structured output contract | 5 | Forced tool call with a strict schema, every field validated, clear INVALID_OUTPUT reasons. |
| 5 | Eval design | 5 | Deterministic checks that catch hallucinated identifiers and invented actions; ANSWER.md says how to grow it (larger labelled set, LLM-as-judge with rubric, human calibration, regression gate in CI). |
| 6 | ANSWER.md trade-offs | 10 | Full: native generative post-contact summary (conversational analytics, enabled via SummaryConfiguration PostContact in the flow block, bundled into Connect Customer pricing) vs custom Bedrock (own format, ServiceNow write, KB links, model choice, extra cost per contact: tokens + guardrail units + KB queries), latency (async after disconnect, not in the agent's path), Step Functions with retries/DLQ vs plain Lambda. Partial: generic. |
Total: 100
