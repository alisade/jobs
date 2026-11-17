# Reference: healthai/w5-c1

Reference: `.grading/solution/retrieval/`. Numbers on the fixtures (recall@5 / MRR):

| setup | overall | exact | paraphrase |
|---|---|---|---|
| bm25 | 0.63 / 0.62 | 1.00 | 0.07 |
| dense | 0.83 / 0.60 | 0.72 | 1.00 |
| hybrid (RRF k=60) | 1.00 / 0.86 | 1.00 | 1.00 |
| hybrid + rerank top 20 | 1.00 / 1.00 | 1.00 | 1.00 |

Why: codes, drug names and policy ids are out of the embedding's vocabulary, so dense search ties across
every policy's section of the same type; paraphrases share no tokens with the text, so BM25 finds nothing.
RRF needs no score calibration between the two. The reranker sees query and document together, so it
fixes ordering (MRR) inside a candidate set that already has the answer; it cannot recover what
retrieval missed, which is why recall is measured before rerank.

Filters: `allowed_ids` runs before ranking. Post-filtering a top-k returns fewer than k results and, with
retired versions tied to current ones, can drop the current version entirely.
