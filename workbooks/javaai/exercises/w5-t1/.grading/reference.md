# Reference: javaai/w5-t1

## Root cause

`ingest()` numbers lessons by their position in `sorted(corpus.glob("*.md"))`. That matched the
front matter only because files were named 01-, 02-, 03- for l1, l2, l3. The content merge added
`00-welcome.md` (front matter `lesson: l0`), which sorts first: welcome became l1, transmission l2,
vaccines l3, antibiotics l4. Every section id shifts, citations link one lesson off, l4 does not
exist (404), and the labeled questions no longer match (recall@3 0.05).

## Red herring

The embedding model changed on 2026-11-11 and the eval stayed at 0.90; the drop follows the content
merge on 2026-11-12. Rolling back the model would cost a full re-embed and fix nothing.

## Fix (`.grading/solution/ingest/build_index.py`)

Use `meta["lesson"]` and `meta["course"]`; raise on a missing or duplicate id. Output is sorted by
file name only for determinism; identity no longer depends on it.

## Follow-ups

Make the eval a blocking Cloud Build step (it already caught this); citation link check; index into
a new version and swap; alert on recall drop; content ids validated in the content repo's CI.
