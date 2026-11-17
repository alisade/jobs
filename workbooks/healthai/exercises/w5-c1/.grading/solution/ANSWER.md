# ANSWER: healthai/w5-c1 Hybrid policy retrieval with rerank

## Approach

Okapi BM25 (k1 1.5, b 0.75), the given dense index, RRF with k=60 over the top 50 of each, filters
(LOB, effective_from <= as_of < effective_to) computed first and passed into both searches, rerank of the
top 20 only.

## Fix

| setup | recall@5 | MRR | exact r@5 | paraphrase r@5 |
|---|---|---|---|---|
| bm25 | 0.63 | 0.62 | 1.00 | 0.07 |
| dense | 0.83 | 0.60 | 0.72 | 1.00 |
| hybrid | 1.00 | 0.86 | 1.00 | 1.00 |
| hybrid + rerank | 1.00 | 1.00 | 1.00 | 1.00 |

BM25 wins exact identifiers, dense wins paraphrases, RRF gets both without calibrating scores, and the
reranker fixes ordering. No query returns a retired version or another LOB's section.

## Trade-offs / what I would do in production

Vector Search hybrid queries with restricts for LOB and numeric filters for dates; the ranking API over
the top 50-100 at a measured latency and cost per 1,000 queries; a labelled set of a few hundred queries
sliced by policy, LOB and kind; retired-version hits as a hard CI gate; versioned indexes swapped
blue-green when policies change.
