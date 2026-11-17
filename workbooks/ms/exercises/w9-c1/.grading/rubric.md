# Rubric: ms/w9-c1 Copilot Studio topics in YAML - password reset, fallback and escalation
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Safety of the reset path | 15 | Full: ownership checked before any flow call, failure fails safe (else branch escalates), no reset for others. Partial: gate present but a path reaches the flow. Zero: no gate. |
| 3 | Orchestration-ready descriptions | 10 | Full: modelDescription says what, when, and what not; trigger phrases varied. Partial: generic description. Zero: missing. |
| 4 | Variable design | 10 | Full: Topic vs Global scopes used deliberately, Global reason defaulted and cleared, System.FallbackCount used. Partial: works but leaks state. Zero: wrong scopes. |
| 5 | YAML fidelity | 5 | Real kinds and property names, ids, `=` formulas, would paste into the code editor. |
| 6 | ANSWER.md trade-offs | 10 | Full: authentication/server-side checks, telemetry, evaluation and ALM considered. Partial: generic. Zero: missing. |
Total: 100
