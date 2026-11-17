# audit/w4-c1 - Durable test run with a human review gate and a hash-chained execution log

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 4 (Mon: durable execution; Tue: review gates; Wed: execution log; Thu: idempotent side effects)

## Scenario

ControlPilot (Meridian Freight Holdings internal audit, fictional) now tests the Q3 CM-03 sample in
one run: for every sampled change it fetches evidence, asks the model-backed tester for the
attribute results, writes a workpaper row to Azure Blob Storage and raises an issue in the GRC system
for every confirmed exception. Exceptions must not be published on the model's word: they wait for
a human reviewer, which can take days.

The first prototype ran in memory. When the worker was recycled halfway, the restart re-ran every
model call (cost), wrote some workpaper rows twice and could not show the external auditor who
overrode what. You are writing the durable version: committed steps are never repeated, side effects
happen exactly once, the reviewer gate is enforced in code, and every step and decision lands in an
append-only log whose integrity can be checked.

Azure Blob and the GRC API are local fakes in `durable/fakes.py` (same error names as the Azure SDK).
The evidence fetcher and the tester are deterministic stand-ins in `durable/agent.py`.

## What you have

| Path | What it is |
|---|---|
| `durable/run.py` | `TestRun`: constructor, crash hook and status helpers given; `run()`, `review()` and `idempotency_key()` are yours |
| `durable/log.py` | `ExecutionLog` and `verify_log()`: yours |
| `durable/store.py` | SQLite `CheckpointStore` (complete): `put_step` commits a step output and the sample state in one transaction |
| `durable/fakes.py` | `FakeBlobContainer`, `FakeGrc`, `CrashInjected` (complete) |
| `durable/agent.py` | `fetch_evidence`, `test_sample` (complete; calls counted in `CALLS`) |
| `fixtures/samples.json` | six sampled changes; two are exceptions (CHG-104390 self-approved, CHG-104502 approved after deploy) |

## Your task

1. **`run()`**. Advance every sample (sorted) as far as it can go; return
   `{"done": [...], "awaiting_review": [...]}`, both sorted. Steps per sample:
   `evidence` (call `evidence_fn`), `test` (call `test_fn`), `review` (only when the test outcome is
   `exception`; the sample stops in state `awaiting_review` and does not block the others),
   `workpaper`, `grc_issue` (only when the final conclusion is `exception`). Commit each step's output
   with `store.put_step(..., state=...)`; a step already committed is never executed again, also
   after a restart (a new `TestRun` on the same db). Call `self._crash(sid, step, "before")` before a
   step's work and `self._crash(sid, step, "after")` after the work but before the commit: the hidden
   tests crash the process at those points and restart it.
2. **Idempotent side effects.**
   - Workpaper: blob `workpaper_blob_name(run_id, sid)` with `overwrite=False`. The row is JSON with
     `run_id, sample_id, control ("CM-03"), attributes, model_conclusion, conclusion, preparer,
     review (the review record or null), evidence`, built only from committed data so a retry
     produces the same bytes. On `ResourceExistsError` compare the stored content: identical is
     success, different raises (never overwrite a workpaper).
   - GRC issue: `grc.create_issue(payload, idempotency_key=idempotency_key(run_id, sid, "grc_issue"))`
     where the key is `f"{run_id}/{sid}/{step}"`, the same on every attempt. Log the intent before
     the call.
3. **Execution log** (`log.py`). JSONL, one record per line:
   `{"seq", "kind", "data", "prev", "hash"}`, `hash = sha256(canonical JSON of seq, kind, data, prev)`,
   `prev` is the previous line's hash (`GENESIS` for the first). Reopening continues the chain.
   `verify_log()` returns a list of problems: an edited, deleted, inserted or reordered line must be
   reported; an intact log returns `[]`. Event kinds the grader looks for: `run_started` /
   `run_resumed`, `step_completed` (data has `sample_id`, `step`), `review` (data has `sample_id`,
   `reviewer`, `decision`, `reason`, `evidence_ref`). Add more if useful.
4. **Review gate** (`review()`). Only a sample in `awaiting_review` can be reviewed, once.
   The reviewer must not be the preparer (compare trimmed, case-insensitive). `decision` is
   `confirm` (conclusion stays exception) or `override` (conclusion becomes pass), and an override
   needs a non-empty `reason` and `evidence_ref`. Violations raise `ReviewError` and change nothing.
   Commit the review as the `review` step (state `reviewed`) and log it. The next `run()` continues
   the sample.
5. **ANSWER.md**: how you made each side effect exactly-once, what the log cannot prove on its own
   (hint: the last lines), and how this maps to a real platform (Durable Functions, Temporal, LangGraph
   checkpointers).

## Acceptance criteria (what the grader checks)

- A crash before or after any step, followed by a restart, finishes with exactly one workpaper per
  sample, exactly one GRC issue per confirmed exception (always the same key), and no committed
  model or test step executed twice.
- Reviews persist across restarts; overrides publish `pass` with the reviewer, reason and evidence
  reference in the workpaper and raise no issue; the review rules raise `ReviewError`.
- An existing workpaper with different content is not overwritten.
- The log chain is contiguous across restarts and `verify_log` flags edits, deletions and reorders.

## How to run

```bash
make setup     # builds audit/.venv once
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade audit/w4-c1
make clean
```
