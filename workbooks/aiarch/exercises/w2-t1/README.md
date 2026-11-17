# aiarch/w2-t1 - The access-review assistant showed another team's reviews

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 2 (Thu: state and sessions)

## Symptom

Since release 2.3.0 three Harbor Point managers have reported that the Lighthouse
access-review assistant answered with people and entitlements from another team. FinOps also
reports that the agent's Bedrock input tokens climb all day and drop back after the nightly
deploy. On-call blames the temperature change in the same release and wants to harden the
system prompt. Read `incident/PAGE.txt` first (created by `make setup`).

## What you have

| Path | What it is |
|---|---|
| `incident/PAGE.txt` | the ticket and on-call notes |
| `incident/app-logs.jsonl` | per-turn logs: session, user, tokens, messages in context, agent object id |
| `incident/transcript-sess-91c2.txt` | the reported conversation |
| `incident/release-2.3.0-notes.md` | what changed in 2.3.0 |
| `service/app.py` | the service the Runtime calls per request (edit this) |
| `service/config.py` | model settings |
| `service/testing.py` | `ScriptedModel`, the offline model used by the tests (works as shipped) |

## Your task

1. Find the root cause from the evidence and the code. Explain the token growth with the same
   cause.
2. Fix `service/app.py`: a session (runtimeSessionId) keeps its own history across turns and
   sees nothing from other sessions; memory stays bounded (`max_sessions` LRU and
   `idle_seconds` expiry, using the injected `clock`); concurrent sessions are safe. Keep the
   `HelpdeskService` interface.
3. Verify with `make test`.
4. Write `ANSWER.md`: Approach, Root cause (with evidence from the logs and code), Fix and
   verification, Trade-offs. Say whether the temperature and the prompt matter.

## Acceptance criteria (what the grader checks)

- Isolation across sessions and service instances, per-session continuity, flat context size,
  LRU bound, idle expiry, concurrent sessions.
- `ANSWER.md` names the shared Agent instance with evidence and dismisses the red herrings.

## How to run

```bash
make setup     # evidence bundle + aiarch/.venv
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade aiarch/w2-t1
make clean
```

## What to submit

`service/app.py` and `ANSWER.md`.
