# connect/w2-c5 - IVR and self-service journey redesign

**Type:** design | **Estimate:** 2 hours | **Study plan:** Week 2 (Tue: customer journey, IVR and self-service design); Week 5 (Lex V2)

## Scenario

LFG's Avaya IVR was built in 2019: a language menu, a six-digit employee ID that is thrown away, a
seven-option main menu where six branches reach the same agents, advice to "reset online" for people who
cannot log in, no ticket status, no callbacks and a dead end after hours. As part of the move to Amazon
Connect the service owner wants a redesigned voice and chat journey, not a lift-and-shift of the tree.
You have the call-tree export, path metrics, survey verbatims and the constraints.

## What you have

| Path | What it is |
|---|---|
| `inputs/current-ivr-map.txt` | the current Orchestration Designer call tree with prompt lengths |
| `inputs/ivr-metrics.csv` | per-path volumes, time in IVR, zero-outs, hang-ups, transfers after answer |
| `inputs/survey-verbatims.txt` | what employees say about the phone line |
| `inputs/constraints.md` | platform, legal, accessibility constraints and the program targets |
| `DESIGN.md` | the template you fill in |

## Your task

1. Diagnose the current IVR with numbers.
2. Design the new journey: principles, journey map, identification and verification tiers, natural
   language vs DTMF with error handling, containment by driver, queue experience, sample prompts,
   accessibility and languages, measurement and rollout, implementation notes for Connect.
3. Fill in `ANSWER.md` with the key changes and expected impact.

## Acceptance criteria (what the grader checks)

- No automated tests: `grade.sh` prints a completeness report and `GRADE_TESTS {"passed": 0, "total": 0}`;
  the rubric carries all 100 points.
- Diagnosis and containment estimates are quantified from `inputs/`; containment is defined so it can
  be measured honestly.
- The design never dead-ends, keeps DTMF and relay access, and is implementable with Connect flows,
  modules, Lex and Lambda within Connect's limits.

## How to run

```bash
make test      # completeness report: which sections are still empty
# then from workbooks/ in Claude Code: /grade connect/w2-c5
```
