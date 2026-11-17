# Rubric: healthai/w6-c1 PHI de-identification for logs, prompts and traces
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 55 | points = 55 * passed / total from grade.sh |
| 2 | Defence in depth | 15 | Minimum-necessary projection first (identifiers never enter the prompt), redaction second, filter on the handler that redacts the formatted message, exceptions and extras; span scrubber on export. No reliance on callers formatting safely. |
| 3 | Precision | 10 | Clinical content preserved (codes, doses, durations, policy ids); patterns anchored so they do not eat ICD codes or "6 weeks". |
| 4 | ANSWER.md | 20 | Honest about regex limits (unknown names in free text), maps each control to Healthcare API de-identify / Sensitive Data Protection infoTypes, explains that a keyed pseudonym is still PHI unless the key is outside the recipient's reach (Safe Harbor vs Expert Determination), key in Secret Manager, the other PHI stores (checkpoints, vector index metadata, eval sets), canary tests in CI. |
Total: 100
