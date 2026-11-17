# connect/w1-c3 - Multi-region resiliency and DR runbook

**Type:** design | **Estimate:** 2 hours | **Study plan:** Week 1 (Fri: Connect Global Resiliency); Week 2 (SLA/SLO and DR design)

## Scenario

LFG's CIO staff classified the new help desk as tier 1: during a regional outage employees still
need password resets and outage reporting, and state examiners ask for a tested DR plan every year.
The security architects will only approve an AWS-supported multi-region pattern. Today everything
(instance, Lambdas, Lex, DynamoDB, recordings) lives in us-east-1. You are the lead architect; the
design review is on Thursday and the CAB wants a runbook it can execute.

## What you have

| Path | What it is |
|---|---|
| `inputs/requirements.md` | RTO/RPO per channel, volumes, staffing, telephony inventory, dependencies, constraints |
| `inputs/incident-history.md` | the three incidents that shaped the requirements |
| `DESIGN.md` | the template you fill in (the deliverable) |
| `ANSWER.md` | approach, key decisions, trade-offs |

## Your task

1. Fill in every section of `DESIGN.md`: architecture with a diagram, telephony and numbers, agents
   and identity, regional dependencies and parity, chat, data continuity, a timed failover/failback
   runbook, testing, cost and risks.
2. Use real Connect mechanisms and name them; where you are unsure a feature exists in the
   secondary region, say how you would verify it rather than assuming.
3. Summarize your key decisions in `ANSWER.md`.

## Acceptance criteria (what the grader checks)

- Graded by rubric only: `grade.sh` prints a completeness report and `GRADE_TESTS {"passed": 0, "total": 0}`;
  the rubric's automated row does not apply.
- ACGR mechanics are correct and complete; every dependency has a secondary-region plan.
- The runbook meets the 15-minute voice RTO with verification and failback steps.
- Gaps (unported DIDs, chat endpoints, vendor dependencies) are called out honestly.

## How to run

```bash
make test        # completeness report: which DESIGN.md / ANSWER.md sections are still empty
# from workbooks/ in Claude Code: /grade connect/w1-c3
```
