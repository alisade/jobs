# Rubric: aiarch/w2-c1 Help desk orchestrator with two Strands specialists
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 55 | points = 55 * passed / total from grade.sh |
| 2 | Guardrails as code | 15 | Full: delete block and audit in hooks on every agent, budget enforced by a hook, nothing relies on prompt wording. Partial: hooks only on one level. Zero: rules in system prompts. |
| 3 | Tool design for a model | 10 | Docstrings say what the tool does and the valid inputs; error messages name the allowed values; outputs trimmed; requester never a tool argument. |
| 4 | Code quality | 5 | Small helpers, no duplicated agent construction, typed signatures. |
| 5 | ANSWER.md | 15 | Hooks vs prompts argued; a reasoned choice between agents-as-tools, swarm, graph and workflow; cost and observability notes. |
Total: 100
