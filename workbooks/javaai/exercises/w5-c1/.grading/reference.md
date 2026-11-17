# Reference: javaai/w5-c1

Files in `.grading/solution/rag/`: `chunking.py`, `retrieve.py`, `metrics.py`, `evaluate.py`.

Reference numbers on the corpus:

| strategy | recall@1 | recall@3 | recall@5 | MRR |
|---|---|---|---|---|
| fixed (40 words, overlap 10) | 0.8438 | 1.0 | 1.0 | 0.9167 |
| heading-aware | 0.875 | 1.0 | 1.0 | 0.9375 |

Why heading-aware wins: chunks match the unit you cite (a section), the heading adds the words
learners use in questions, and no chunk mixes two sections' vocabulary. Fixed windows straddle
sections, so the cited section is sometimes wrong even when the text is right.

## Points worth making

- With 32 questions one question moves recall@1 by 3.1 points; the difference here is one question.
  More labels before declaring a winner; report per-course numbers.
- Filter first: `WHERE course_id = $1 ORDER BY embedding <=> $2 LIMIT k` in pgvector, metadata filters
  in RAG Engine / Agent Search. Post-filtering a global top-k returns fewer than k and is a leak risk
  if someone forgets it.
- recall@5 saturates on a small corpus; recall@1 and MRR are the useful signals here.
- Gate in CI on any change to chunking, embedding model, index parameters; baseline changes go
  through review like code.
