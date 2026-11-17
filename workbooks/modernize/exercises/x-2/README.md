# modernize/x-2 - Blast radius and rollback for corvane-commons 3.0 (Jakarta)

**Type:** design (optional add-on) | **Estimate:** 2 hours | **Study plan:** Week 7 (add-on: blast radius and parallel change on shared libraries)

## Scenario

The platform team at Corvane Mutual wants to release corvane-commons 3.0: Jakarta EE 10, JDK 17
baseline, and no more 2.x. Seven consumers depend on it in different ways: WARs on EAP 7.4 and
EAP 8, a Spring Boot 2.7 batch, a Spring Boot 3 service, a .NET API that parses its JSON over
HTTP, and data extracts that read its tables directly. 3.0 also carries an irreversible DDL
change on a 410-million-row audit table that every consumer migrates at startup. The architecture
board has asked you, as the ClaimDesk modernization lead, for the blast-radius assessment and the
rollout plan before it approves ARCH-212.

## What you have

| Path | What it is |
|---|---|
| `inputs/corvane-commons.md` | what the library contains, its javax exposure, its DB objects, the 3.0 proposal |
| `inputs/consumers.md` | the seven consumers, versions, usage, pipelines |
| `inputs/calendar.md` | windows, freezes, team plans, DBA constraints |

## Deliverables

1. `DESIGN.md`: change summary and recommendation; a blast-radius table (consumers and shared
   assets); sequencing with parallel change and dual publishing of javax and jakarta artifacts;
   detection per risk; a rollback per step; go/no-go gates; open questions.
2. `ANSWER.md`: the key decisions and what you would push back on.

## Acceptance criteria (rubric)

- Every consumer and every shared asset (DB objects, REST/JSON contract, JMS, pipelines with version
  ranges) appears with a concrete impact.
- The sequence keeps every consumer deployable at every step and fits the calendar.
- Each risk has a detection method; each step has a rollback, including the irreversible DDL.

## How to run

```bash
make setup      # nothing to install
make test       # completeness report (rubric-graded, no tests)
# from workbooks/ in Claude Code: /grade modernize/x-2
make clean
```
