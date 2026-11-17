# Rubric: ms/ai-t1 Policy assistant cites the wrong documents after the re-index
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause | 30 | Full: query path pins hash-bow-v1 while the index manifest says hash-bow-v2; same dims so no error, similarities meaningless. Partial: "embedder changed" without identifying the query/index split. Zero: blames chunk size, the corpus or the model. |
| 3 | Evidence | 15 | Full: cites manifest vs app config, the collapsed top-k scores (about 0.04 vs about 0.4 before), and an experiment (e.g. v2 query on the v2 index restores 1.0; v1 at chunk 120 still 1.0, ruling out chunk size). Partial: config diff only. Zero: assertion without evidence. |
| 4 | Fix quality | 15 | Full: config aligned AND a startup guard on embedder name and dims with an actionable message; no false positive on a matching pair. Partial: config only, or guard that only checks dims. Zero: neither. |
| 5 | Production trade-offs | 10 | Full: ship index and query config as one versioned artifact, eval gate in the release pipeline, record the embedding model in index metadata, Azure AI Search: one model deployment for embedding skill and vectorizer, alert on score distribution drift. Partial: one or two. Zero: none. |
Total: 100
