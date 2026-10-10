# connect/w3-c3 - Hybrid coexistence and number porting cutover plan

**Type:** design | **Estimate:** 2-3 hours | **Study plan:** Week 3 (Tue: BYOC and coexistence; Fri: porting, cutover and rollback)

## Scenario

LFG is moving its IT help desk from Avaya Aura (US and Canada) and Genesys Engage (London) to
Amazon Connect Customer in four agent waves between December 2026 and May 2027. Back-office
users stay on Avaya behind the new Voice Connector trunk. The CIO wants one document the
telephony team, the Pune NOC, the carriers and the AWS account team can execute: how both
platforms coexist, how every help desk number moves, and what happens if a port goes wrong.
The account team has already said a Voice Connector-into-Connect bridge is not an approved
pattern for LFG.

## What you have

| Path | What it is |
|---|---|
| `inputs/number-inventory.csv` | every number, carrier, current platform and target, call volume |
| `inputs/current-state.md` | platforms, carriers, sites, teams, how context flows today |
| `inputs/constraints.md` | waves, freezes, availability limits, decisions already made |
| `DESIGN.md` | the template you fill in (the deliverable) |

## Your task

1. Fill in every section of `DESIGN.md`. Ground each Connect, Voice Connector and porting
   statement in AWS documentation (the porting pages, "Region requirements for ordering and
   porting phone numbers", conversational analytics for external voice systems, the Chime SDK
   pages on Voice Connector and on migrating PSTN audio to Connect).
2. Fill in `ANSWER.md`: your approach, the five decisions that matter most, and the
   alternatives you rejected.

## Acceptance criteria (what the grader checks)

- Graded by rubric only (`.grading/grade.sh` prints a completeness report and
  `GRADE_TESTS {"passed": 0, "total": 0}`; the rubric's automated row does not apply).
- Coexistence architecture uses documented patterns only (no invented Connect SIP trunk).
- Context passing works in both directions without relying on SIP headers over the PSTN.
- Porting plan respects documented lead times and windows and the LFG freezes.
- Cutover runbook with gates and owners; parallel run with exit criteria; rollback that is
  honest about what can be undone after a port.

## How to run

```bash
make test      # completeness report: which DESIGN.md / ANSWER.md sections are still empty
# then from workbooks/ in Claude Code: /grade connect/w3-c3
```
