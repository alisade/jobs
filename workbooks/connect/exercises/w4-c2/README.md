# connect/w4-c2 - Migration program plan for the LFG help desk

**Type:** design | **Estimate:** 2-3 hours | **Study plan:** Week 4 (migration playbooks, coexistence, cutover and rollback, migration factory); Week 9 (offshore delivery, hypercare and KT)

## Scenario

LFG's steering committee approved moving the IT help desk from four platforms (Avaya Aura voice,
Genesys Engage chat, Five9 outbound and overflow, the acquired Ridgeway desk on Cisco UCCE/CVP)
to Amazon Connect. You are the lead architect for the consultancy and own the migration program
plan the committee will sign. It has to survive three contract dates, a year-end change
blackout, carrier porting lead times and a delivery team split across onshore, Pune and
Monterrey.

## What you have

| Path | What it is |
|---|---|
| `inputs/current-state.md` | platforms, volumes, telephony, integrations, constraints and people |
| `DESIGN.md` | the template you fill in (the deliverable) |

## Your task

1. Fill in every section of `DESIGN.md`: goals and success criteria, waves with dates and
   entry/exit criteria, coexistence during migration, the migration factory, validation and
   testing, cutover runbook, rollback plan, RACI, hypercare/KT/decommissioning, risks and decisions.
2. Use the numbers and dates in `inputs/`; when something cannot be met (it can't, all of it),
   say so and propose the trade-off.
3. Fill in `ANSWER.md` (Approach, Fix = summary of your key decisions, Trade-offs).

## Acceptance criteria (what the grader checks)

There are no automated tests (grade.sh reports 0/0). The rubric scores: wave strategy against the
real dates, coexistence and telephony realism, validation gates, cutover and an honest rollback
(ports are not quickly reversible), the offshore delivery model, and hypercare/KT/decommission
including recording retention.

## How to run

```bash
make setup
make test      # completeness report: which sections are still empty
# from workbooks/ in Claude Code: /grade connect/w4-c2
make clean
```
