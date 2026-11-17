# Rubric: awsfde/w2-c1 AgentCore Runtime entrypoint with per-tenant, per-user Memory
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Trust boundary and isolation | 20 | Full: tenant/actor/session only from validated claims and the runtime header; validation of claim values before they reach Memory; payload identity fields ignored and logged; ANSWER.md explains that decoding without verifying is only safe behind the runtime's customJWTAuthorizer and what breaks if it is removed. Partial: isolated in code but unexplained. Zero: any identity from the payload. |
| 3 | Runtime contract | 10 | Full: correct status codes, ping busy/idle with time_of_last_update only on change, in-flight tracking that is thread-safe and decremented in finally. Partial: works single-threaded only or leaks the busy state on errors. |
| 4 | Failure handling | 10 | Full: throttling degrades with a logged event; misconfiguration (AccessDenied) is loud; no bare except. Partial: everything degrades silently. |
| 5 | ANSWER.md production thinking | 10 | Full: concrete on at least three of: IAM condition keys bedrock-agentcore:namespace / namespacePath on the runtime role, event expiry, OTel/Observability spans, caller-side session id lifetime, ARM64 container and port, streaming (SSE). Partial: generic. |
Total: 100
