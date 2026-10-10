# connect/w2-c4 - Help desk transformation solution design document

**Type:** design | **Estimate:** 3 hours | **Study plan:** Week 2 (all days: discovery, journeys, routing, WFM, omnichannel, consulting deliverables)

## Scenario

You are the Perficient lead architect on LFG's Enterprise Help Desk Transformation. Discovery is done
(`inputs/`): 182 agents across Charlotte, Pune and Monterrey on Avaya Aura voice, Genesys chat and
Five9 notifications, ServiceNow ITSM and Okta SSO, with a signed-off requirements list and hard
constraints (four months to a production pilot, a change freeze, the Avaya renewal decision). The
steering committee and the offshore build team will review your solution design document next week.

## What you have

| Path | What it is |
|---|---|
| `inputs/current-state.md` | organization, platforms, volumes, KPIs, pain points |
| `inputs/requirements.md` | business outcomes (B*), functional (F*) and non-functional (N*) requirements |
| `inputs/constraints.md` | team, timeline, freeze, AWS landing zone, porting lead times, budget |
| `DESIGN.md` | the document template you fill in (15 sections) |

## Your task

1. Write the solution design in `DESIGN.md`: architecture with a diagram, journeys, identity tiers,
   routing and a staffing estimate from the given peak, ServiceNow/Okta integration patterns, AI and
   self-service with evaluation, analytics and QA, security and retention, resiliency and operations,
   delivery plan with migration/cutover and a RACI with the offshore team, risks/ADRs, cost model.
2. Trace every requirement to a design element and a measure.
3. Fill in `ANSWER.md` with your approach and the key decisions.

## Acceptance criteria (what the grader checks)

- No automated tests: `grade.sh` prints a completeness report and `GRADE_TESTS {"passed": 0, "total": 0}`;
  the rubric carries all 100 points.
- The design uses current Connect capabilities by their current names and no unsupported patterns,
  sizes the peak with numbers, and has a credible delivery and cutover plan with rollback.
- Every requirement is traced; risks, decisions and cost are explicit.

## How to run

```bash
make test      # completeness report: which sections are still empty
# then from workbooks/ in Claude Code: /grade connect/w2-c4
```
