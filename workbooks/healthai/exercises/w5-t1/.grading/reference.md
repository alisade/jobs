# Reference: healthai/w5-t1

Root cause: `chunking/chunker.py` v2 splits the markdown into 60-word windows with a 10-word overlap,
ignoring structure. Criteria rows (~25 words) straddle window boundaries, lines are reflowed into one
string, continuation chunks have no header row ("Criterion | Requirement | Step therapy"), and the section
path is the heading at the window start. Row queries drop to 0.56 recall@5 while text queries stay 1.00.
Evidence: `make chunks P=KHP-MP-0101` shows a chunk starting "for infliximab: ... | step therapy 3 weeks |
| 2.e |"; missed ids include KHP-MP-0101-2.d, KHP-MP-0611-2.d, KHP-MP-0903-2.f.

Red herring: the embedding upgrade. The canary ran the bm25-only pipeline and got the same 0.67; the
local eval has no embeddings at all and reproduces it.

Fix: `.grading/solution/chunking/chunker.py`: blocks by heading and by table/prose runs; tables split
between rows with the header repeated; prose grouped by paragraph to max_words. recall@5 0.667 -> 1.0.
