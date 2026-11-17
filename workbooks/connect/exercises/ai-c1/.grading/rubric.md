# Rubric: connect/ai-c1 Guarded LLM triage with an eval gate
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Injection defense in depth | 15 | Full: untrusted text only in the user turn with a boundary the caller cannot close, static system prompt, guardrail on, AND deterministic post-model guards (the model proposes, code decides); explains why the prompt alone is not a control. Partial: prompt hardening only. |
| 3 | Budget and fallback design | 10 | AbortController/abortSignal or race with cleanup, budget below the flow's InvocationTimeLimitSeconds with headroom, no SDK retries that outlive the budget, fallback that routes to a human. |
| 4 | Eval harness quality | 10 | Metrics defined precisely (what counts as correct, fallback handling, injection containment), failures actionable with ids and reasons, gate thresholds explicit. |
| 5 | ANSWER.md judgement | 15 | Full: reads `make eval` honestly (gate fails: accuracy 0.75, fallback 0.25), attributes each failure (truncation -> maxTokens or shorter summary; VPN -> category definitions; injection case -> wrong category but contained), proposes concrete next steps (prompt/category definitions, tool use or structured output, re-record and re-run, online sampling, red-team set growth), and gives per-contact latency/cost reasoning. Partial: lists metrics without interpretation. |
Total: 100
