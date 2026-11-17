# Rubric: ms/ai-c1 Contoso Parts ordering agent - tools, loop and server-side guardrails
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 45 | points = 45 * passed / total from grade.sh |
| 2 | Tool design | 15 | Full: descriptions say when to use, what returns, limits, and that notes are data; tight schemas (pattern, bounds, additionalProperties false); place_order references a quote only. Partial: correct schemas, thin descriptions. Zero: vague or permissive tools. |
| 3 | Guardrail placement | 15 | Full: policy enforced in execute_tool against session state set by the app (confirm), not by the model or prompt; no path lets model text create a confirmation; double orders blocked. Partial: enforcement present but bypassable (e.g. trusts a model-supplied flag). Zero: relies on the system prompt. |
| 4 | Loop robustness | 10 | Full: history invariant always holds (truncated and turn-limit calls answered), tool exceptions contained, ordered parallel results, usage summed. Partial: one gap. Zero: crashes on bad input. |
| 5 | ANSWER.md and production thinking | 15 | Full: explains injection defence in depth (schema limit, quote policy, out-of-band confirmation), maps to Copilot Studio tools / Foundry function tools, names what is still missing (idempotency, rate limits, audit, telemetry, human-in-the-loop for high value). Partial: describes the code only. Zero: missing. |
Total: 100
