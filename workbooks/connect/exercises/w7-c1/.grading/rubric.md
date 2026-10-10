# Rubric: connect/w7-c1 ServiceNow incident Lambda for the help desk flow
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Budget and failure semantics | 15 | Full: one deadline threaded through every call; Retry-After honored only when it fits; bounded retries; 401 refresh exactly once; every ServiceNow failure becomes DEGRADED (flat map) so the flow can route with context; ANSWER.md relates the 6.5 s budget to Connect's 8 s sync limit and its own retry behavior. Partial: works but budget checked in only some places, or retries unbounded in principle. Zero: sleeps past the budget or throws into the flow. |
| 3 | Idempotency | 10 | Full: lookup-before-create on correlation_id across all pages, and ANSWER.md names the remaining race (two concurrent invokes both see "none") with a real fix (DynamoDB conditional put keyed by ContactId, or ServiceNow-side unique constraint / scripted REST endpoint that upserts). Partial: guard only, race not discussed. |
| 4 | Security and hygiene | 10 | Credentials only in the form body; secret from Secrets Manager/Parameter Store (not env plaintext) in the production notes; encoded-query injection neutralized; least-privilege ServiceNow role; no PII in logs. |
| 5 | Code quality | 5 | Typed, small functions, client separate from orchestration, no dead code, no any-typed responses leaking to the flow. |
| 6 | ANSWER.md production trade-offs | 10 | Full: at least three positions: async invoke or after-contact creation via EventBridge for slow ServiceNow, token cache scope and rotation, ServiceNow rate-limit rules per integration user, observability (structured logs with ContactId, metrics for DEGRADED), VPC/NAT or no-VPC choice. Partial: generic. |
Total: 100
