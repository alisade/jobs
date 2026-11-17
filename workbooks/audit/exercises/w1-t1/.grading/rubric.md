# Rubric: audit/w1-t1 Every change passes after the prompt v2 rollout
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 35 | points = 35 * passed / total from grade.sh |
| 2 | Root cause | 25 | Full: prompt v2 renamed the attribute keys (approval_precedes_deploy, approver_independent, ci_green); the response_schema was dropped from the request so the model followed the prompt's names; the contract ignores unknown keys (extra="ignore") and defaults the three attribute flags to True, so every renamed flag became a pass with zero validation errors. Partial: names the defaults or the renamed keys but not how they combine. Zero: temperature or model version. |
| 3 | Evidence | 15 | Full: quotes a freeform recording (e.g. S07 with approval_precedes_deploy false), the contract lines, the diff hunk that removed response_schema, and before/after run output. Partial: asserts without output. |
| 4 | Fix quality | 15 | Full: strict facts-only contract (no defaults, extra forbid), schema on the request, attributes decided in code from timestamps and the directory (S21 cross-time-zone case right), so the model's flags are not trusted. Partial: restores the schema or removes defaults, but still trusts the model's booleans. |
| 5 | Red herrings and impact | 10 | Full: rules out temperature (it changes wording, not key names; validation_errors=0 shows parsing "succeeded") and the model bump (constrained recordings from the same model are right); states that all CM-03 conclusions since 2026-10-06 need re-performance and that prompt and contract changes need change control and an eval gate. Partial: one of these. |
Total: 100
