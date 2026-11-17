# Rubric: audit/w1-c1 Structured CM-03 evidence extraction with Gemini, Pydantic and a validation retry
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Contract design | 10 | Full: no defaults on evidence fields, extra=forbid, AwareDatetime, pattern and enum constraints, field descriptions the model can use. Partial: strict but no descriptions or one leniency left. Zero: defaults that turn a missing key into a passing value. |
| 3 | Loop robustness and control | 15 | Full: one bounded loop; disallowed tools never executed; tool errors returned as function responses; validation errors fed back verbatim; non-retryable finish reasons stop; nothing raises to the caller. Partial: works but retries blindly or swallows errors without recording them. |
| 4 | Facts vs conclusions | 10 | Full: attribute decisions are pure code over typed facts (instants compared in UTC, identities resolved through the directory), the model never decides pass/fail; ANSWER.md explains why this matters for an auditor. Partial: correct code, no reasoning. |
| 5 | Auditability and production thinking | 15 | Full: ANSWER.md names what to log per call (model version, prompt/config hash, request and response, usage, retries, tool calls), how needs_review items reach a human, cost per sample from usage, and what changes before running quarterly samples. Partial: generic logging advice. |
Total: 100
