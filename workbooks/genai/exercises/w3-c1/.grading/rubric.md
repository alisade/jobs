# Rubric: genai/w3-c1 Assistant agent endpoint with a confirm-before-write tool
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Enforcement in code, not prompt | 15 | Full: the write path is structurally impossible from the loop (the loop has no call to `start_return`); only `confirm` executes it; stored args are whitelisted. Partial: relies on checking a flag the model can set, or on the system prompt. |
| 3 | Authorization model | 10 | Ownership checked on every order access with one indistinguishable error; conversation ownership; confirm bound to user + conversation; 404 rather than 403 for other users' actions. |
| 4 | Loop robustness and auditability | 10 | Bounded turns, errors as `is_error` with actionable messages, output cap, an audit entry for every decision including denials. |
| 5 | ANSWER.md | 15 | Full: where pending actions live in production (shared store with TTL so any replica can confirm), passing the customer's token downstream (not a service superuser), what the UI shows (the server's summary, not model text), audit retention, rate limits on proposals, and how this maps to the lethal trifecta. Partial: generic. |
Total: 100
