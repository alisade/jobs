# modernize/ai-t1 - The headless migration agent costs 4x: prompt caching never hits

**Type:** troubleshooting | **Estimate:** 1.5 hours | **Study plan:** AI Integration page (context engineering and caching) and Week 6 (headless agents in CI)

## Symptom

The ClaimDesk pod runs its migration agent headless in CI, one job per Maven module. Each job
sends a large, mostly static system prompt (instructions, the module's file listing, two skills)
on every turn, with a prompt-caching breakpoint on it. FinOps flagged spend at 4x the 4-week
average since 2026-11-05. Job count and duration are flat. One developer blames the model bump
that shipped the same day. Read `evidence/PAGE.txt` first.

## What you have

| Path | What it is |
|---|---|
| `evidence/` | the FinOps alert and thread, the usage dashboard export, the git log of `migrate_agent/`, the pricing note for the model bump, a replay of a recorded session |
| `migrate_agent/prompt.py` | builds each turn's request (yours to fix) |
| `migrate_agent/fake_api.py` | an offline model of prompt-caching accounting (read its docstring; do not change it) |
| `migrate_agent/session.py` | replays a recorded 8-turn session through `build_request` and the fake API |
| `skills/` | the two skills the agent loads |

No API key or network is used anywhere.

## Your task

1. Find the root cause and prove it with the evidence and `make replay`: what makes the cached
   prefix differ from one request to the next. Find every source of instability, including the
   ones that only bite across CI processes. Rule the model bump in or out.
2. Fix `build_request` so the cached prefix is byte-identical across turns, processes and runs of
   the same module, while the model still gets the current time for its change log. Keep the
   signature.
3. Write `ANSWER.md`: Approach, Root cause (commands and output excerpts), Fix (and how you
   verified it), Trade-offs / production follow-ups, including the guard that would have caught this.

## Acceptance criteria (what the grader checks)

- The cached prefix (everything up to the last `cache_control`) is identical across different
  times, file-listing orders and skill orders; it still holds the instructions, listing and skills.
- The current time still reaches the model, after the breakpoint.
- Different modules do not share a prefix.
- The replay reads the cache on every turn after the first, and its cost drops well below the baseline.
- `ANSWER.md` names the mechanisms with evidence; "use a cheaper model" does not pass.

## How to run

```bash
make setup
make replay     # usage per turn for the current build_request
make test       # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade modernize/ai-t1
make clean
```
