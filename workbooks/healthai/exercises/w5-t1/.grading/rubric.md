# Rubric: healthai/w5-t1 The chunker splits a criteria table mid-row
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause and evidence | 35 | Full: chunker v2's fixed 60-word windows with 10-word overlap cut criteria rows across chunks and reflow lines, and continuation chunks lose the table header and get the section path of wherever the window started; quotes a mid-row chunk (`make chunks` or the agent log citation) and at least two missed row queries; row recall 0.56 vs text 1.00. Partial: "chunking" without mechanism or evidence. Zero: blames the embedding model. |
| 3 | Red herring ruled out with evidence | 15 | Uses the bm25-only canary row (same 0.67, no embeddings involved) or reproduces locally with the BM25-only eval, so the embedding upgrade cannot explain it. |
| 4 | Fix quality and prevention | 20 | Structure-aware chunker (headings, whole rows, header repeated, section path), numbers after the fix; prevention: one retrieval change per release, an eval gate per change, chunk-level invariant tests in CI, mention of Document AI layout parser or parent-child chunks. |
Total: 100
