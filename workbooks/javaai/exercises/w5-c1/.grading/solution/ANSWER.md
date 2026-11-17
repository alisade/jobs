# ANSWER: javaai/w5-c1 Retrieval eval

## Approach

Wrote the metrics first and checked them on hand examples (duplicates, partial recall, no hit),
then the chunkers on a toy lesson, then the filtered search, then evaluate and gate.

## Fix

make run:

    fixed    {"n": 32, "recall@1": 0.8438, "recall@3": 1.0, "recall@5": 1.0, "mrr": 0.9167}
    heading  {"n": 32, "recall@1": 0.875, "recall@3": 1.0, "recall@5": 1.0, "mrr": 0.9375}
    GATE PASS

Heading-aware wins because chunks align with the citation unit and headings add question words;
fixed windows straddle sections. 13/13 tests.

## Trade-offs / what I would do in production

32 questions is small (one question is ~3 points), so label more and report per course. recall@5
saturates here; watch recall@1 and MRR. Next: hybrid keyword + vector, a reranker, the same eval
against RAG Engine and pgvector. The filter is applied before ranking because it is access control.
The gate runs in CI on chunking, embedding or index changes; the baseline only moves in a reviewed PR.
