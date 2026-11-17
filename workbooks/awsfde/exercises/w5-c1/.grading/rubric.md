# Rubric: awsfde/w5-c1 Supply-chain graph: openCypher queries and a tenant-safe graph tool
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 55 | points = 55 * passed / total from grade.sh |
| 2 | Query quality | 15 | Full: idiomatic openCypher that would run unchanged on Neptune (parameters, not string concatenation; DISTINCT where paths multiply rows; direction of ORDERED right; q3 bounded variable length), every node scoped. Partial: correct results but scoping only on the anchor node, or literal values. |
| 3 | Tool safety design | 15 | Full: no model-supplied query text, allow-listed templates and argument patterns, tenant from ctx only, static scoping check before sending, timeout and row cap; errors are ToolError the model can act on. Partial: validation present but tenant or text can still come from the model in some path. |
| 4 | ANSWER.md production thinking | 15 | Full: shared graph vs per-tenant graph trade-off (Neptune Analytics graphs are sized and billed by memory; per-tenant graphs isolate but multiply cost), IAM auth (SigV4) and private connectivity, Neptune Database (transactional, clusters) vs Analytics (in-memory analytics, vector similarity), when a graph is overkill, GraphRAG via Knowledge Bases. Partial: generic. |
Total: 100
