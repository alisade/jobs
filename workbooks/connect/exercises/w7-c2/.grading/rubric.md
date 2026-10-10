# Rubric: connect/w7-c2 Agent workspace app: handoff context, guided resolution and agent assist
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Contact lifecycle correctness | 15 | Full: tracks the current contactId, ignores stale async results and clears for other contacts, resets per contact, unsubscribes with the same handler references. Partial: works in tests but relies on effect re-runs or stale closures that would double-subscribe in StrictMode. |
| 3 | Data minimization and safety | 10 | Requests HANDOFF_KEYS only, renders no unrelated attribute, entitlement default-deny for unknown departments, sys_id validated, no secrets in the browser (token from a getter backed by the agent's session). |
| 4 | Ranking design | 10 | Dedupe/tie rules deterministic and explained; ANSWER.md says where entitlements come from in production (IdP groups, agent hierarchy, security profile tags) and how to evaluate ranking (click-through, resolution rate). |
| 5 | Code quality | 5 | Typed props and state, small pure functions for rank/guide/parse, accessible roles/labels. |
| 6 | ANSWER.md production notes | 10 | Full: 3P app registration and iframe permissions, Amazon Connect SDK provider init, backend auth tied to the agent identity, step-by-step guide vs custom app trade-off, telemetry. Partial: generic. |
Total: 100
