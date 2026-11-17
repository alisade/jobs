# Rubric: ms/w10-c1 Agent release gate for the Fabrikam support agent
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 45 | points = 45 * passed / total from grade.sh |
| 2 | Correct evaluation semantics | 15 | Full: missing transcripts are failures not skips, malformed data never crashes, None vs 0 handled deliberately, inclusive thresholds, tolerance boundaries exact. Partial: one of these handled by accident or via try/except-everything. Zero: silent skips or crashes. |
| 3 | Code quality | 10 | Full: small pure functions, report is plain JSON-serializable data, no duplicated metric logic, clear reasons strings. Partial: works but tangled. Zero: hard to follow or mutates inputs. |
| 4 | Release decision in ANSWER.md | 15 | Full: blocks the candidate and names the real drivers with numbers (web citations collapsing grounded_rate, saf-04 injection obeyed with a StartReturn call, missing war-02 and malformed record, p95 latency). Partial: says block without evidence or misses the safety regression. Zero: ships it or no decision. |
| 5 | Production trade-offs | 15 | Full: discusses code-graded vs LLM-judged evaluators (Copilot Studio compare meaning / Foundry Groundedness, Tool Selection), test-set size and flakiness (repeat runs, confidence), telemetry in Application Insights (customEvents, designMode) for post-release monitoring, wiring the gate into ALM via the evaluation REST API. Partial: two of these. Zero: none. |
Total: 100
