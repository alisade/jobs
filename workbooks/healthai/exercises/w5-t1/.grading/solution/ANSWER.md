# ANSWER: healthai/w5-t1 The chunker splits a criteria table mid-row

## Approach

Ran `make eval` (0.667; rows 0.556, text 1.0) and `make chunks P=KHP-MP-0101`, then compared with the
eval history: the bm25-only canary also shows 0.67.

## Root cause

Chunker v2 cuts fixed 60-word windows with 10-word overlap. Criteria rows straddle windows, lines are
reflowed, continuation chunks lose the header row and get the section path of the window start. Example
chunk: "for infliximab: ... | step therapy 3 weeks | | 2.e | ...". Missed: KHP-MP-0101-2.d,
KHP-MP-0611-2.d, KHP-MP-0903-2.f. The embedding upgrade is a red herring: BM25-only reproduces the drop.

## Fix

Structure-aware chunker: never cross headings, full heading path, tables split only between rows with
the header repeated, prose grouped by paragraph up to 120 words. recall@5 0.667 -> 1.0.

## Trade-offs / what I would do in production

One retrieval change per release with an eval gate each; chunk invariant tests in CI; Document AI
layout parser for real PDFs; parent-child chunks for long tables; evaluate the embedding upgrade on its
own before keeping it, since re-embedding the corpus is not free.
