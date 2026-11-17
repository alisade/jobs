# Rubric: ms/w1-t1 Nightly ERP load failed and the ForEach never ran
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause | 30 | Full: firstRowOnly defaulting to true after PR #412 dropped the property, so Lookup output has firstRow and no value array, failing the ForEach items expression. Partial (15): "Lookup/ForEach expression problem" without explaining the output shape or why it changed. Zero: throttling, permissions, or only the column rename. |
| 3 | Evidence | 15 | Quotes the ForEach InvalidTemplate error, the Lookup output showing firstRow, and the removed line in the PR #412 diff. Explains the latent column rename (schema_name -> source_schema) found while verifying. |
| 4 | Red herring handled | 10 | Explains why the DTU recommendation / slow SalesOrderLine copy is not the cause (it was a successful earlier run; no Copy started in the failed run). |
| 5 | Fix quality and verification | 10 | Minimal fix to the definition (no hard-coded list, no schema change), verified with the dry run and a plan for a safe prod rerun (watermark semantics). |
| 6 | Production trade-offs | 5 | At least two concrete preventions: test stage in a deployment pipeline, Fail activity carrying the real error, freshness alert, bounded incremental window. |
Total: 100
