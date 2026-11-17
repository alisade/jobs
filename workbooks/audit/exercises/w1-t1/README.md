# audit/w1-t1 - Every change passes after the prompt v2 rollout

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 1 (Wed: structured outputs and Pydantic contracts; Fri: validation and retry)

## Scenario

ControlPilot tested the Q3 2026 sample for CM-03 (program change) at Meridian Freight Holdings
(fictional) on release 2026.10.2. The run report says **25 of 25 samples pass, 0 exceptions, 0
validation errors**. Last quarter the same control produced 3 exceptions in 25. The senior reviewer
re-performed five samples by hand and found two exceptions that ControlPilot scored as pass, and
refuses to sign the workpaper. The team chat has theories (the temperature change, the new model
version). The audit manager wants the actual cause, a fix, and an explanation that an external
auditor would accept, because every CM-03 conclusion since 2026-10-06 is now in doubt.

The Gemini calls are replayed from recordings by `controlpilot/fake_gemini.py` (read its docstring:
it answers the way the live model did for the request you send). No API key, no network.

## What you have

| Path | What it is |
|---|---|
| `controlpilot/` | the release 2026.10.2 code: prompt, contract, pipeline |
| `run.py` | `make run` replays the Q3 run and prints the report |
| `fixtures/` | the 25 samples, the prod deploy log, the identity directory, the recordings |
| `evidence/` | release notes, the config diff from 2026.9.4, the Q3 run log, the Q2 report, the reviewer's spot check, the team chat |

## Your task

1. Reproduce the symptom with `make run`.
2. Find the root cause. Prove it with evidence from the code, the recordings and the diff (quote
   what you ran and what it printed). Rule the team's theories in or out with evidence.
3. Fix it so that the run finds the real exceptions and cannot fail this way silently again. A
   missing or renamed key must never turn into a passing attribute.
4. Write `ANSWER.md`: approach, root cause with evidence, fix and how you verified it, and what you
   would tell the audit manager about the conclusions issued since 2026-10-06.

## Acceptance criteria (what the grader checks)

- The Q3 run reports the real exceptions (and only those), with the failed attribute named.
- The request constrains the output with a schema; the contract rejects missing and unknown keys.
- A freeform response with the v2 key names can never become a pass.
- Attribute conclusions do not depend on the model's own judgement of the timestamps.
- `ANSWER.md` names the root cause and backs it with evidence; red herrings are ruled out.

## How to run

```bash
make setup
make run       # reproduce
make test      # visible test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade audit/w1-t1
make clean
```
