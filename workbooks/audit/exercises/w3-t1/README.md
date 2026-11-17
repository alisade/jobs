# audit/w3-t1 - After the nightly restart the agent re-tests finished samples

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 3 (Tue: ADK sessions, state and state prefixes)

## Scenario

ControlPilot's nightly CM-03 job at Meridian Freight Holdings (fictional) runs on Google ADK with a
persistent session (`DatabaseSessionService` on SQLite; Cloud SQL in production). Each night a new
process resumes the same session, `cm03-2026Q3`, and tests the next batch of five changes from the
10-change Q3 sample, so the sample is done in two nights.

Reviewers report that after the second night their queue has **two work items for the same
exception**, and the night-two log shows the same changes being tested again. Nothing has failed
and no errors were raised. The on-call engineer points at the `Skipping missing token usage metadata`
warnings and at a GRC 429 retry in the log. The audit manager needs to know whether night-two
results can be trusted and how many reviewer hours were wasted.

The model is a deterministic stand-in (`nightly/policy_llm.py`) driven through the real ADK Runner.
No network.

## What you have

| Path | What it is |
|---|---|
| `nightly/batch.py` | one nightly invocation: resume the session, run the agent |
| `nightly/tools.py` | `next_batch` and `test_change`, with the progress tracking |
| `nightly/queue.py` | the reviewer work queue and a record of every test performed (SQLite) |
| `nightly/policy_llm.py` | the model stand-in (do not edit) |
| `incident/` (after `make setup`) | stdout and logs of two nights run as separate processes, and the queue report |
| `run/` | the session database and the queue database those two nights produced |

## Your task

1. `make setup` runs two nights. Read `incident/` and inspect `run/sessions.db` (the session state
   is in the database: look at what ADK persisted after each invocation).
2. Find the root cause and prove it: show what state existed during night one and what was
   persisted. Rule the warnings and the 429 in or out.
3. Fix it so a restarted process resumes where the previous invocation stopped.
4. `ANSWER.md`: root cause with evidence, fix and verification, and the impact (which results and
   work items are duplicates, what to tell reviewers). Mention which ADK state scope you chose and why.

## Acceptance criteria (what the grader checks)

- Two nights in separate processes test each of the 10 changes exactly once.
- Exactly one work item per exception; a third night tests nothing.
- Progress is stored in a scope that ADK persists.
- `ANSWER.md` names the root cause with evidence from the session database or a reproduction.

## How to run

```bash
make setup     # venv + two nights + incident/
make run       # one more pair of nights on the same run/ (after make setup)
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade audit/w3-t1
make clean
```
