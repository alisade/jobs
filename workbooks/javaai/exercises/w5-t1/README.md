# javaai/w5-t1 - The tutor cites the wrong lessons after a content release

**Type:** troubleshooting | **Estimate:** 1-1.5 hours | **Study plan:** Week 5 (Mon: chunking and metadata; Thu: retrieval evals as gates)

## Symptom

Since this morning the Microbiology tutor cites lessons "one off": the vaccines answer links to the
antibiotics lesson, and some links 404. The release-checklist retrieval eval dropped from 0.90 to
0.05 recall@3 on the content merge, but the gate is advisory and nobody looked. The ingest job
release the day before also changed the embedding model; L2 wants to roll it back and re-embed
everything (4 hours). Start with `incident/PAGE.txt`.

## What you have

| Path | What it is |
|---|---|
| `incident/` | page, release notes, eval history, sample citations |
| `ingest/build_index.py` | the ingestion job (markdown to index rows) and the search used by the tutor |
| `ingest/eval.py` | the release-checklist eval (`make run`) |
| `ingest/embed.py` | embedding stand-in (do not change) |
| `corpus/` | the course content after the merge, and labeled questions |

## Your task

1. Find the root cause and prove it: compare stored ids with each file's front matter, and run the
   eval with and without the new file.
2. Rule the embedding-model theory in or out with evidence.
3. Fix ingestion so ids never depend on file names or order: ids come from front matter, a lesson
   without an id or a duplicate id fails the job loudly, re-ingest is idempotent.
4. `make test`, then write `ANSWER.md` (Approach, Root cause with evidence, Fix and verification,
   Trade-offs / production follow-ups, including making the eval a blocking gate).

## Acceptance criteria (what the grader checks)

- Ids from front matter; renaming or reordering files changes nothing.
- Missing or duplicate lesson ids raise.
- recall@3 >= 0.9 on the corpus; idempotent index output with unique chunk ids.
- Root cause and evidence in `ANSWER.md` match the incident.

## How to run

```bash
make setup
make run       # the eval
make test
# from workbooks/: /grade javaai/w5-t1
make clean
```
