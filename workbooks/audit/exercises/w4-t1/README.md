# audit/w4-t1 - Duplicate GRC issues after a retry

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 4 (Mon: durable execution; Thu: idempotent side effects and commit-then-timeout)

## Symptoms (as reported)

> From: K. Brooks (IT audit manager, MFH) - Thu 2026-10-01 08:40
>
> The overnight publish run for CM03-2026Q3 finished "6 published, 0 failed", but the GRC shows
> **three** open issues for CHG-104390 and **two** for CHG-104611, all with the same title. The
> workpaper also has CHG-104390 twice. The external auditors pull the GRC issue list on Monday; a
> duplicated exception reads as two control failures. The platform team says the GRC gateway was
> rate-limiting us overnight and that we should ask for a higher quota. Can you find out what
> actually happened and make sure it cannot happen again?

ControlPilot's publish stage (`orchestrator/run.py`) appends one workpaper row per tested sample to
the run's Azure append blob and raises one GRC issue per confirmed exception, through the GRC client
in `orchestrator/grc_client.py`. `orchestrator/fakes.py` contains faithful local fakes of the GRC
issues API and the append blob (the fault behaviour in there is how the real gateway behaved that
night; the bug is not in the fakes).

## What you have

`make setup` replays the 02:00 UTC run with the faults the gateway recorded and writes `incident/`:

| File | What it is |
|---|---|
| `incident/orchestrator.log` | ControlPilot publish-stage log |
| `incident/grc-gateway.log` | GRC gateway access log: request ids, Idempotency-Key, result |
| `incident/grc-issues.json` | issues the GRC holds for the run |
| `incident/workpaper.jsonl` | the workpaper append blob |
| `incident/checkpoint-dump.txt` | the orchestrator's checkpoint table |

## Your task

1. Find the root cause. Correlate the orchestrator log with the gateway log by time and request id;
   explain each extra issue and the extra workpaper row. Rule the rate-limiting theory in or out
   with evidence.
2. Fix the code so that retries (client-level and step-level) and a process restart can never
   create a second issue or a second workpaper row for the same sample of the same run, while a
   new run (a new quarter) still raises its own issues. Keep the 429 handling.
3. `make replay` and `make test`; write `ANSWER.md` (approach, root cause with log excerpts, fix and
   how you verified it, what you would change in production).

## Acceptance criteria (what the grader checks)

- With timeouts after commit, lost requests, 429s and a worker crash after the GRC committed (then a
  restart on the same checkpoint db), every exception has exactly one GRC issue and every sample
  exactly one workpaper row.
- A new run id still creates new issues; re-running a finished run is a no-op.
- `ANSWER.md` names the actual cause with evidence from both logs and rules the red herring out.

## How to run

```bash
make setup     # venv + incident/ bundle
make test      # visible tests
make replay    # re-run the incident scenario against your code
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade audit/w4-t1
make clean
```
