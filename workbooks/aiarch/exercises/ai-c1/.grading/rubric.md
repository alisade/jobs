# Rubric: aiarch/ai-c1 Change-management MCP server
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 55 | points = 55 * passed / total from grade.sh |
| 2 | Identity and security | 15 | Token verified before tools exist, no identity arguments, comment permissions from groups, nothing echoes secrets. |
| 3 | Tool design for a model | 10 | Task-shaped tools, descriptions with valid inputs, actionable errors, trimmed outputs, pagination, annotations. |
| 4 | Code quality | 5 | Typed arguments instead of hand parsing, small helpers, no duplicated lookups. |
| 5 | ANSWER.md | 15 | Five concrete rules mapped to code, a correct deployment story (Runtime MCP contract or gateway target, audience validation, OBO not passthrough). |
Total: 100
