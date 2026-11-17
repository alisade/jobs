# javaai/w5-c1 - Retrieval eval for the course tutor: chunking, recall@k, MRR and a CI gate

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 5 (Mon: chunking and metadata; Tue: pgvector vs RAG Engine; Thu: retrieval metrics and CI gates); shared core section 5 (evals)

## Scenario

Before Kestrel lets anyone judge generated tutor answers, retrieval has to be measured: does the
right lesson section come back for a learner's question? You own the offline harness that will
run in CI on every change to chunking, embeddings or the index. The corpus is two open courses
(microbiology, statistics) with 32 questions labeled with the section that answers each.

The embedding model is a deterministic stand-in (`rag/embed.py`, hashed bag of words) so the eval
is reproducible offline; in production the same harness calls the Vertex AI text embedding model
and pgvector or RAG Engine.

## What you have

| Path | What it is |
|---|---|
| `corpus/*.md`, `corpus/questions.jsonl` | lessons (front matter, `##` sections) and labeled questions |
| `rag/corpus.py`, `rag/embed.py` | loader and embedder (do not change) |
| `rag/chunking.py` | `fixed_chunks`, `heading_chunks` (TODO) |
| `rag/retrieve.py` | `Index.search` with a course filter (TODO) |
| `rag/metrics.py` | `dedupe`, `recall_at_k`, `reciprocal_rank` (TODO) |
| `rag/evaluate.py` | `evaluate`, `gate` (TODO) and `main` (`make run`) |
| `baseline.json` | the stored baseline the gate compares against |

## Requirements

1. **Chunkers** (docstrings have the exact rules): fixed windows with overlap over the whole lesson,
   citing the section that contributes most words; heading-aware chunks with a
   "title - heading:" prefix, split at `max_words`. Stable unique `chunk_id`s, course and lesson kept.
2. **Search**: cosine top-k, ties by `chunk_id`, filtered to the learner's course before ranking
   (this filter is access control).
3. **Metrics at section level**: duplicates of a section count once; recall@k over distinct
   sections; reciprocal rank of the first relevant distinct section.
4. **evaluate**: mean recall@1, @3, @5 and MRR over the questions, 4 decimals.
5. **gate**: fail when any baseline metric is more than `tolerance` below it or missing; return reasons.
   `python -m rag.evaluate` prints both strategies and exits 1 when the heading strategy fails the gate.

## Acceptance criteria (what the grader checks)

- Hand-computed metric cases (duplicates, partial recall, no hit).
- Exact chunk windows, overlap, citations and ids on a toy lesson; heading prefix and split.
- Course filter never leaks; ranking sensible.
- On the corpus: heading-aware chunking beats fixed-size on MRR and is not worse on recall@1;
  the CLI gate passes.
- `ANSWER.md`: your numbers for both strategies, what you would add next (hybrid search,
  reranking, more labeled questions, per-course breakdown) and how the gate runs in CI.

## How to run

```bash
make setup
make test
make run       # the report and the gate
# fill in ANSWER.md, then from workbooks/: /grade javaai/w5-c1
make clean
```
