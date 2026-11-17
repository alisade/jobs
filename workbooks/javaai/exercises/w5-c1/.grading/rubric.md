# Rubric: javaai/w5-c1 Retrieval eval for the course tutor: chunking, recall@k, MRR and a CI gate
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 55 | points = 55 * passed / total from grade.sh |
| 2 | Metric correctness and clarity | 10 | Section-level dedupe before cutting at k, recall defined over relevant sections, MRR on distinct sections; small pure functions with docstrings. |
| 3 | Access-control thinking | 10 | Filter before ranking (not post-filtering a global top-k, which can return fewer or leak); ANSWER.md ties it to per-course or per-learner metadata filters in pgvector (WHERE clause) or RAG Engine / Agent Search filters. |
| 4 | Results and interpretation | 15 | ANSWER.md reports both strategies with numbers, explains why heading-aware wins (chunks align with citation units, headings add vocabulary), notes 32 questions gives wide uncertainty (one question = ~3 points), and proposes next steps: more labels, hybrid keyword + vector, a reranker, per-course breakdown. |
| 5 | CI gate design | 10 | Gate on stored baseline with a tolerance, explicit reasons, missing metric fails; baseline updated only by a reviewed change; runs on changes to chunking, embedding model or index config. |
Total: 100
