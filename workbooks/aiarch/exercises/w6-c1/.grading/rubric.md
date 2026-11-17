# Rubric: aiarch/w6-c1 SSM Automation rollback runbook
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 60 | points = 60 * passed / total from grade.sh |
| 2 | Operational safety | 15 | Backup before mutation, no-op path, approval message with both versions, bounded wait, verification after the change. |
| 3 | Parameter hygiene | 5 | Patterns or allowed values on every input that reaches an API. |
| 4 | ANSWER.md | 20 | Least-privilege assume-role policy, cross-account execution model, CDK deployment, a reasoned Change Manager position. |
Total: 100
