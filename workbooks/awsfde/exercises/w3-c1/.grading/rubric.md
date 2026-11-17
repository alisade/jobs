# Rubric: awsfde/w3-c1 Retrieval eval harness and a tenant-filtered Retrieve call
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Tenant filter design | 15 | Full: one builder, tenant filter from the verified tenant only, user filters ANDed (never OR at top level), recursive rejection of tenant_id in user filters, andAll minimum handled. Partial: correct for flat filters only. Zero: tenant filter optional on any path. |
| 3 | Metric correctness and report quality | 10 | Full: document-level dedupe, per-tenant breakdown, leaks listed with ids, rounding consistent, compare symmetric. Partial: chunk-level metrics or missing breakdown. |
| 4 | Interpretation in ANSWER.md | 15 | Full: quotes both runs (fixed ~0.725 recall@5 with one leak on q09, hierarchical ~0.95 with none), says the gate result, treats the leak as a security finding to investigate in the real KB (untagged or mis-tagged sidecar, ingestion, filter code) independent of the chunking decision, recommends hierarchical with caveats. Partial: numbers without reasoning. |
| 5 | Production thinking | 10 | Full: harness in CI on every KB or chunking change, golden set ownership and growth from real failures, limits of 20 questions (confidence), generation-side evals (groundedness, Bedrock RAG evaluation), cost of re-ingestion. Partial: generic. |
Total: 100
