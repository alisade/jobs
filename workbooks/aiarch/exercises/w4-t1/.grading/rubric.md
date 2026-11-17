# Rubric: aiarch/w4-t1 Contractor approved another team's request
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause | 35 | Full: policy2 errors on the missing team attribute for partner tokens, erroring policies are skipped, so policy1's permit stands. Partial: "missing team" without the skip semantics. Zero: ENFORCE broken or permit ordering. |
| 3 | Evidence | 15 | Decision log fields (determining policy1, errors on policy2) for AR-1187 and the earlier LOG_ONLY AR-1102; claims without team. |
| 4 | Fix quality | 10 | `has` guard inside the forbid so missing team denies; schema validation passes; no policy removed. |
| 5 | Production view | 10 | Validation in CI, alarms on evaluation errors, LOG_ONLY review covering errors, IdP mapping, second layer in the API. |
Total: 100
