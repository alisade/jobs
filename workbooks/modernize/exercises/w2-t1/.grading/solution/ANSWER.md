# ANSWER: modernize/w2-t1 The reverse-engineer skill missed the batch job's tables

## Approach

Read the page, then the transcript. Checked what the tool returned before judging the model.

## Root cause

`jq 'select(.type=="tool_result") | .lines' incident/transcript.jsonl` gives 200. A full run gives 314
hits (`scan_db.py repo --limit 100000 | wc -l`). The 200th line is in claims-web: `scan()` sorts by path
and `render()` returned `lines[:limit]` with no total and no marker, so every reporting-batch hit was
cut. `grep -rl LOSS_TRIANGLE repo` lists only reporting-batch files. The spec lists the 9 tables the
model was shown; the repo has 14. The model then claimed absence for reporting-batch without proof,
and the skill invited that ("record every table it reports"). The postmortem is wrong: run_stats show
31% context use, and a bigger model would have received the same 200 lines.

## Fix

scan_db.py: `summarize()` (all tables, counts, modules, never paged) printed first; `render()` states
`total=` and `shown=` and ends with `# TRUNCATED: N more hits ... --offset K` when cut; `--offset`
flag. SKILL.md: read the summary, page on TRUNCATED, inventory must equal the summary, absence claims
need proof. Verified with the tests and by re-running the scan: the summary lists 14 tables with
reporting-batch.

## Trade-offs / what I would do in production

Failure-mode log: "2026-10-28 INC-7731: tool truncated silently at 200 lines; agent claimed absence.
Fix: summary + explicit truncation; coverage check in skill; eval repo larger than one page." Add an
eval case for the skill with a repo that exceeds one page, and apply the same rule to every tool in the
harness: totals first, explicit partial results, actionable continuation.
