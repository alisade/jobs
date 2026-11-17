# Rubric: healthai/w5-c1 Hybrid policy retrieval with rerank, measured
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 55 | points = 55 * passed / total from grade.sh |
| 2 | Correctness of the retrieval pieces | 15 | Okapi BM25 and RRF implemented from the formulas, filters applied before ranking (not post-filtering a top-k), rerank limited to the head, deterministic tie-breaks. |
| 3 | Measurement | 15 | ANSWER.md has the full table (four setups x overall/exact/paraphrase x recall@5/MRR) with numbers that match the code, and reads it correctly: BM25 wins exact terms, dense wins paraphrase, fusion gets both, rerank fixes ordering (MRR) more than recall. |
| 4 | Production judgement | 15 | Maps to Vector Search hybrid queries and restricts/numeric filters, the ranking API over top 50-100, cost/latency per 1,000 queries, labelled-set size and slices, retired-version count as a hard gate, index versioning and blue-green swaps. |
Total: 100
