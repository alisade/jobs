# healthai/w4-t1 - A reviewer's decision lands on another member's case

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 4 (Wed persistence, threads and interrupts; Week 1 Mon asyncio)

## Scenario

Kestrel Health Plan's (fictional) review UI posts nurse and medical director decisions to a small async
service that resumes the case's LangGraph thread from its checkpoint. After release 2026.11.3, a nurse
reports that their approval for one member appeared on a different member's determination letter, and a
medical director's denial did too. Letters were held before mailing; Privacy wants to know whether data
crossed between cases. Read `incident/ticket.md`.

## What you have

| Path | What it is |
|---|---|
| `incident/ticket.md`, `incident/audit-export.jsonl` | the report and the audit trail of the replayed burst (`make setup`) |
| `pa_graph/review_service.py` | the service as released |
| `pa_graph/graph.py` and friends | the PA graph (the reference from w4-c1; treat it as correct unless you find otherwise) |
| `scripts/repro.py` | `make repro` replays three reviewers submitting at the same moment |
| `findings.json` | your machine-checked findings |

## Your task

1. Reproduce with `make repro` and read the audit export: for each submission, which thread did it
   resume?
2. Find the root cause and test the app team's theory (thread id derived from the member) against the
   code and the evidence.
3. Fix the service so concurrent submissions always resume their own thread. Add a guard that fails
   loudly if a resume ever returns a determination for a different case.
4. Fill in `findings.json` (file, symbol, whether the thread-id scheme is the cause, the case ids that got
   wrong determinations in the replay) and `ANSWER.md`, including what Privacy should be told.

## Acceptance criteria (what the grader checks)

- Bursts of concurrent decisions (several random interleavings) each land on their own case and
  member; every thread finalizes exactly once by the right reviewer; audit receipts match.
- No module-level, per-request-mutated run config remains.
- `findings.json` matches the evidence.

## Run

```
make setup && make repro && make test
# fill in ANSWER.md and findings.json, then: /grade healthai/w4-t1
make clean
```
