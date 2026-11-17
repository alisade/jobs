# healthai/w5-c1 - Hybrid policy retrieval with rerank, measured

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 5 (Tue hybrid search and RRF; Wed reranking and retrieval evals)

## Scenario

Kestrel Health Plan's (fictional) criteria agent retrieves medical-policy sections before it checks a
PA case. Today it uses dense search only. Nurses report two failure modes: queries that name a policy id,
HCPCS code or drug ("KHP-MP-0101 reauthorization") get a neighbouring policy's section, and some answers
cite a retired policy version, which in UM is a correctness bug, not a quality issue. You will build
hybrid retrieval (BM25 + dense, fused with reciprocal rank fusion), metadata filters applied before
ranking, an optional rerank of the top candidates, and the retrieval eval that proves each step helps.

## What you have

| Path | What it is |
|---|---|
| `fixtures/corpus.json` | 84 synthetic policy sections across 10 KHP policies; some have a retired `v2` with `effective_to` |
| `fixtures/queries.json` | 100 labelled queries (`kind`: `exact` or `paraphrase`, `lob`, `as_of`, `gold` section id) |
| `retrieval/text.py`, `embed.py`, `rerank.py` | given: tokenizer, an offline embedding stub (concept vectors; codes and ids are out of vocabulary) and a stub cross-encoder. Do not change them |
| `retrieval/search.py` | `BM25Index`, `DenseIndex` (given), `rrf`, `allowed_ids`, `HybridRetriever` (finish the TODOs) |
| `retrieval/evaluate.py` | `recall_at_k`, `reciprocal_rank`, `evaluate` (implement) |
| `scripts/build_corpus.py` | how the fixtures were generated |

## Your task

1. `BM25Index`: Okapi BM25 with `k1=1.5`, `b=0.75`, `idf = ln(1 + (N - df + 0.5) / (df + 0.5))`; only
   positive scores; ties by id; honour `allowed`.
2. `rrf(ranked_lists, k=60)`: `score(d) = sum 1 / (k + rank)`, rank starting at 1, sorted by score then id.
3. `allowed_ids(docs, lob, as_of)`: the section's `lobs` contains `lob`, and
   `effective_from <= as_of < effective_to` (`effective_to` null means open-ended).
4. `HybridRetriever.retrieve(query, lob, as_of, k, mode, rerank)`: filter first, then rank
   (`bm25`, `dense`, or `hybrid` = RRF of both candidate lists); if `rerank`, rescore only the top
   `rerank_top_n` with `reranker.score(query, text)`; unknown mode raises `ValueError`.
5. `evaluate(retriever, queries, k, **kwargs)`: `{"recall@k", "mrr", "n", "by_kind": {...}}` (the key is
   literally `recall@5` for k=5).
6. In `ANSWER.md`, put the table of recall@5 and MRR for bm25, dense, hybrid and hybrid+rerank, overall
   and per kind, and explain it.

## Acceptance criteria (what the grader checks)

- BM25 matches the Okapi formula; RRF matches the formula; date and LOB filters exact at the boundaries.
- No query in any mode ever returns a retired section or one for another line of business, and
  filtering happens before top-k.
- Hybrid recall@5 >= 0.95 and clearly above both BM25 and dense; per-kind slices show why.
- Rerank lifts MRR to >= 0.95 while scoring at most `rerank_top_n` pairs per query.

## Run

```
make setup && make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade healthai/w5-c1
make clean
```
