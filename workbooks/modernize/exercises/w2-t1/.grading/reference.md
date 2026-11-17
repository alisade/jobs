# Reference: modernize/w2-t1

Root cause: `scan_db.py render()` returned `lines[:limit]` with limit 200 and no indication that it had
cut anything. `scan()` sorts by path, so claims-core and claims-web filled the 200 lines and all 114
reporting-batch hits (LOSS_TRIANGLE, IBNR_FACTOR, REINS_TREATY, BORDEREAU_RUN, IBNR_RESULT, plus its
CLAIM/RESERVE_LINE use) were dropped. The transcript shows `lines: 200`, the model listed exactly the 9
tables it saw, and then over-claimed that reporting-batch has no DB access. Context use was 31%, so the
context-window theory is wrong; a bigger model would have seen the same 200 lines.

Fix: `.grading/solution/skill/reverse-engineer/scripts/scan_db.py` (always-complete summary, paged list with
header totals and a `# TRUNCATED ... --offset N` line) and the SKILL.md verification step (inventory equals
summary; absence claims need the summary line).

Lesson for agent tools: return totals, say when output is partial and how to get the rest, and put the
complete aggregate before the detail.
