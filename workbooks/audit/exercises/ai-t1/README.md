# audit/ai-t1 - Gemini cost up over 4x and latency up after the prompt refactor

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** AI Integration page (3 Context and caching; 7 Observability); Week 6 Wed (cost and latency per control)

## Symptoms (as reported)

> From: FinOps alert, Wed 2026-10-07 06:00 UTC - "ControlPilot Gemini spend +274% day over day"
>
> From: R. Alvarez (ControlPilot lead) - 08:15
>
> The nightly CM-03 batch cost per 100 samples went from about $0.08 to about $0.30 and p50 latency
> per call from ~180 ms to ~830 ms. Yesterday's release had three changes: the prompt builder cleanup,
> the model bump to gemini-3.8-flash-002 and a second Function instance. My bet is the new model
> version: maybe it tokenizes differently or is not covered by caching yet. Can you confirm and
> tell us whether to roll back the model?

ControlPilot builds every Gemini request in `promptkit/prompt.py` and runs the batch with
`promptkit/runner.py`. The model endpoint is replaced by `promptkit/fake_gemini.py`, which simulates
Gemini **implicit caching** faithfully enough for this incident: read its docstring before you start.
The simulator, the runner and the pricing table are not the bug.

## What you have

`make setup` writes `incident/`:

| File | What it is |
|---|---|
| `incident/usage-before.jsonl` | per-call usage of the 2026-09-29 batch (recorded before the release) |
| `incident/usage-after.jsonl` | per-call usage of the 2026-10-07 batch, replayed against the current code on two instances |
| `incident/cost-dashboard.txt` | the summary FinOps looked at |
| `incident/release-notes.md` | what changed on 2026-10-06 |

## Your task

1. Find the root cause from the usage logs and the request the code builds (instrument it: print or
   diff `fake_gemini.serialize_request()` for two samples, and for one sample in two processes).
2. Decide whether the model bump is involved, with evidence.
3. Fix the request builder so the cache works again for every sample, every run and every instance,
   without removing any tool or changing the system instruction's content. `make replay`, `make test`.
4. Write `ANSWER.md`: root cause with evidence (usage numbers, the prefix that differs), the fix and
   how you verified it, and how you would keep this from regressing (a test or an alarm).

## Acceptance criteria (what the grader checks)

- The tools-plus-system prefix is byte-identical across samples, runs and Python processes with
  different `PYTHONHASHSEED`; nothing per-request (run id, start time, sample id) is in it.
- The sample data is in the last user content; the request contract (tools, temperature, JSON) is unchanged.
- The batch is back to a cache hit ratio of about 0.9 or more, across two instances too, with cost per
  100 samples and p50 latency back at the 2026-09-29 baseline.
- `ANSWER.md` names both parts of the cause and rules the model bump in or out with evidence.

## How to run

```bash
make setup     # venv + incident/
make test      # visible tests
make replay    # re-run the after batch against your code (two instances)
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade audit/ai-t1
make clean
```
