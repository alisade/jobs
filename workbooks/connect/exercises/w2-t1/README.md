# connect/w2-t1 - Password-reset service level collapsed after a "copy" routing change

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 2 (Wed: routing strategy; Fri: KPI analysis); Week 1 (Wed: routing profiles, priority and delay)

## Symptom

Friday 2026-10-09, the LFG service desk ops manager pages the platform team: PasswordReset service
level has been red all week (about 70% against an 85% target, abandons tripled) while General and
Applications look fine. Same headcount as last week apart from two agents in training on
Wednesday. Supervisors say agents sit in Available while password-reset callers wait "only for a
few seconds". The only platform change was CHG0032015 on Sunday, a routing profile consolidation
described as "a straight copy of the existing settings". Read `incident/PAGE.txt` first.

## What you have

| Path | What it is |
|---|---|
| `incident/PAGE.txt`, `incident/CHG0032015.txt`, `incident/roster-notes.txt` | the page, the change record, the roster |
| `incident/historical-metrics.csv` | per day and queue, 08:00-10:00 ET peak: queued, handled, abandoned, SL 30 s, ASA, max wait, AHT, staffed |
| `incident/ctr/<date>.jsonl` | contact records for both weeks (one JSON per line; queue and agent timestamps) |
| `incident/realtime-snapshot-2026-10-06-0856.txt` | real-time queue dashboard export |
| `incident/routing-profiles-before-CHG0032015.json`, `incident/routing-profiles-prod-2026-10-09.json` | routing profile exports (queue configs) |
| `config/routing-profiles.json`, `config/users.json` | what you change: the routing profiles and user assignments to deploy |
| `tools/` | the LFG routing model and the week's caller streams. Treat it as the environment (Connect itself), not the suspect |

## Your task

1. Find the root cause. Prove it from the data, not just the diff: what the contact records show
   about when password-reset callers get answered, and why "available agents while callers wait"
   is consistent with it.
2. Fix it forward in `config/` (the consolidation stays; do not roll users back to the old profiles).
3. Verify with `make replay` (the week of 2026-10-05 replayed with your config) and `make test`.
4. Write `ANSWER.md`: Approach, Root cause (commands and output excerpts), Fix (and the replay
   numbers before and after), Trade-offs / production follow-ups (how a change like this should be
   reviewed and tested before it ships).

## Acceptance criteria (what the grader checks)

- Week replay: PasswordReset SL >= 82%, abandon <= 8%, ASA <= 12 s; General >= 80%; Applications >= 85%;
  the training day recovers too.
- The consolidation is kept: 26 agents on rp-service-desk with all three queues; rp-apps and media
  concurrency unchanged; profiles valid. `tools/` unchanged.
- The root cause in `ANSWER.md` names the mechanism and is backed by evidence from the bundle; the
  red herring is ruled out with numbers. A fixed config with a hand-waved explanation does not pass.

## How to run

```bash
make setup     # links the toolchain and generates incident/
make replay    # replay the week with config/ (run it before and after your change)
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade connect/w2-t1
make clean
```

Useful: `jq -r 'select(.Queue.Name=="PasswordReset" and .Agent != null) | .Queue.Duration' incident/ctr/2026-10-06.jsonl | sort -n | uniq -c | head -30`
