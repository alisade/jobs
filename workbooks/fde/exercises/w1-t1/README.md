# fde/w1-t1 - cache_read_input_tokens collapsed after a "harmless" release

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 1 (Thu: prompt caching); AI Integration area 3 (context engineering and caching)

## Symptom

Bramblewood Gear's shopping agent (built on the commerce-agents blueprint's prompt layout)
shipped release 2026.10.06 this morning. By the afternoon finance paged on-call: Claude
spend is 2.4x baseline on flat traffic, the prompt-cache hit rate dropped, and time to first
token is up. Every change in the release was reviewed as harmless, and the pre-deploy cache
check passed. Read `incident/PAGE.txt` first.

## What you have

| Path | What it is |
|---|---|
| `incident/PAGE.txt` | the page and the on-call thread |
| `incident/release-notes-2026.10.06.md`, `incident/release-2026.10.06.diff` | what shipped |
| `incident/previous_release/` | the code and flags of release 2026.09.29 (yesterday) |
| `run/logs/2026-10-05/`, `run/logs/2026-10-06/` | one log per API worker process (16), one `log_model_call` line per model call (created by `make setup`) |
| `run/dashboard.txt` | the cache panel export for both days |
| `storefront_prompt/` | this checkout: the code running in prod now |
| `config/flags.json` | prod flags |
| `replay/` | a replay of the traffic through 16 worker processes and a cache simulator with the Messages API's prefix semantics. Treat it as the environment, not the suspect. |

## Your task

1. Find the root cause. Prove it with evidence from the logs and from the code, not just
   the diff: which bytes differ, between what, and why the pre-deploy check did not see it.
2. Fix it in `storefront_prompt/` without losing what the release was for (INC-2291 dedupe,
   `extra_tools`).
3. Verify: `make test` and `make replay` (the dashboard for this checkout should look like
   yesterday's again).
4. Write `ANSWER.md`: Approach, Root cause (with the commands you ran and output excerpts),
   Fix (and how you verified it), Trade-offs / production follow-ups (how you would stop
   this class of bug from shipping again).

## Acceptance criteria (what the grader checks)

- Every worker process sends byte-identical tools + static system text for the same flags,
  whatever its hash seed.
- Tool order is the order release 2026.09.29 shipped; an extra tool takes its release slot;
  a name enabled twice appears once; an unknown extra still fails fast.
- Replayed traffic reads from cache like the previous release (> 80% overall, > 85% on the
  first call of turn 2+).
- Nothing per-request sits before a breakpoint.
- The root cause in `ANSWER.md` names the actual mechanism and is backed by evidence. A
  fixed system with a hand-waved explanation does not pass.

## How to run

```bash
make setup     # shared venv + replays both days into run/ (about a second)
make test      # visible checks
make replay    # after a fix: replay this checkout's code, print its dashboard
# from workbooks/: /grade fde/w1-t1
make clean     # removes run/
```

Useful: `grep -h 'turn=2 round=1' run/logs/2026-10-06/*.log | head`,
`PYTHONHASHSEED=1 python -c ...` vs `PYTHONHASHSEED=2 python -c ...`.
