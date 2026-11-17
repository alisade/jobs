# healthai/w5-t1 - The chunker splits a criteria table mid-row

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 5 (Mon structure-aware chunking; Wed retrieval evals)

## Scenario

Release 2026.11 of Kestrel Health Plan's (fictional) policy retrieval shipped two changes at once: a new
chunker and an embedding model upgrade. Since then the criteria agent says step-therapy criteria are "not
found in policy", and the weekly retrieval eval dropped from 0.98 to 0.67 recall@5. The ML team wants to
roll back the embedding model. Read `incident/ticket.md` and find the real cause first.

## What you have

| Path | What it is |
|---|---|
| `incident/` | ticket, release notes, eval history, criteria agent log |
| `policies/*.md` | six synthetic KHP medical policies with criteria tables |
| `fixtures/queries.json` | 48 labelled queries (36 criteria-row, 12 text) |
| `chunking/chunker.py` | chunker v2, as released (`chunk_policy(markdown, policy_id)`) |
| `chunking/search.py`, `chunking/evaluate.py` | BM25-only retrieval and the eval (given) |
| `findings.json` | your machine-checked findings |

## Your task

1. `make eval` and `make chunks P=KHP-MP-0101`; decide which release change explains the drop, with
   evidence, and rule the other in or out.
2. Rewrite `chunk_policy(markdown, policy_id, max_words=120)` so that it is structure-aware:
   - chunks never cross a heading; `section_path` is the full heading chain
     (`"KHP-MP-0101 Infliximab ... > Coverage criteria > Criteria table"`), starting with the policy id
   - tables become `kind="table"` chunks that are split only between rows, and every table chunk starts
     with the header row and the separator row; table and prose lines never share a chunk
   - prose is grouped by paragraph up to `max_words`; no text is lost; lines are kept intact
3. `make eval` again; fill in `findings.json` (component, at least two missed query ids as evidence, the
   red herring, recall@5 before and after) and `ANSWER.md`.

## Acceptance criteria (what the grader checks)

- Every criteria row is whole in exactly one chunk, for every policy, also with a small `max_words`.
- Table chunks repeat the header; section paths are right; no chunk crosses a heading; nothing is lost.
- recall@5 >= 0.95 with all row queries hit; `findings.json` consistent with the evidence.

## Run

```
make setup && make eval && make test
# fill in ANSWER.md and findings.json, then from workbooks/ in Claude Code: /grade healthai/w5-t1
make clean
```
