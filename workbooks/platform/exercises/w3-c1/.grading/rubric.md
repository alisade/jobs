# Rubric: platform/w3-c1 Import blocks from a Cloud Asset Inventory export
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Correctness of IDs and skip rules | 15 | Full: every import ID format right, IAM member IDs space separated, Google-managed identities and service agent roles skipped on both paths, state IDs skipped. Partial: one category missing. |
| 3 | Determinism and code quality | 10 | Full: sorting and collision handling independent of input order, small mapping functions or a table, no fixture-specific branches. Partial: works but order-dependent logic. |
| 4 | ANSWER.md and migration method | 25 | Full: places the tool in a method (inventory, group by owner and blast radius, small batches, generate config, cleanup by schema, no-op plan gate, lock out manual change with IAM/org policy), compares with bulk-export and terraform query list blocks, discusses `google_project_iam_member` vs authoritative `google_project_iam_binding`/`policy` during migration, plan for unsupported types. Partial: generic. |
Total: 100
