# connect/w6-c3 - QA and compliance monitoring program (design, optional)

**Type:** design | **Estimate:** 2 hours | **Study plan:** Week 6 (evaluation forms, automated and generative AI evaluations, rules and categories, calibration, coaching)

## Scenario

Larkspur's service desk moves to Amazon Connect with 140 agents across Charlotte, an offshore vendor
in Pune and a nearshore vendor in Monterrey. Three QA analysts hand-score 2% of calls on a spreadsheet,
vendor QA scores its own agents 9 points higher on the same calls, chat is not reviewed at all, and an
agent asking a caller for their password went unnoticed for a week. The CIO wants "every contact
checked for the things that can hurt us, humans only where it matters". You are the lead architect:
design the QA and compliance monitoring program on Amazon Connect conversational analytics (formerly
Contact Lens) and evaluation forms, integrated with ServiceNow.

## What you have

| Path | What it is |
|---|---|
| `inputs/current-state.md` | volumes, people, requirements, platform facts |
| `DESIGN.md` | the template you fill in (the deliverable) |
| `ANSWER.md` | short cover note |

## Your task

Fill in every section of `DESIGN.md` and the `ANSWER.md` cover note. Use the platform's documented
capabilities (conversational analytics rules and categories, real-time and post-contact analytics,
evaluation forms, automated evaluations through rules, generative AI performance evaluations,
calibration, EventBridge events, tasks) and say where you need custom code.

## Acceptance criteria (what the grader checks)

Graded by rubric only (no automated tests; `grade.sh` reports 0/0 plus a completeness report):

- Every DESIGN.md section filled, with the tables and the diagram asked for.
- Detection rules map to the stated risks with the right trigger (real-time vs post-contact) and action.
- Sampling arithmetic fits analyst capacity; automation vs human split is justified and validated.
- Calibration makes vendor and LFG scores comparable; disputes and coaching have owners and SLAs.
- Privacy: redacted vs original data, access by site, retention, real-time handling.
- A rollout plan with risks.

## How to run

```bash
make test      # completeness report only
# then from workbooks/ in Claude Code: /grade connect/w6-c3
```
