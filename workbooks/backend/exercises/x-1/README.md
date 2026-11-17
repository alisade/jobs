# backend/x-1 - Timed whiteboard: a self-serve workflow automation service

**Type:** design | **Estimate:** 1.5 hours (45 minutes timed, then review) | **Study plan:** Week 7 add-on (Thu-Fri: timed mock sessions); Week 6 (Thu: workflow primitives)

## Scenario

Second round of the Lumenfold interview loop: a 45-minute system design session with two Keystone
engineers. The prompt is in `inputs/prompt.md`. In the real session they will interrupt you around
minute 30 with harder questions; here those are in `inputs/curveballs.md`. Do not open it early.

## Rules of the session

1. Set a 45-minute timer. Read only `inputs/prompt.md`.
2. Write `DESIGN.md` the way you would speak at the whiteboard: short sentences, decisions with a
   reason, numbers where they matter, a diagram. Do not polish; this is about the method under time.
3. At minute 30, open `inputs/curveballs.md` and answer each one in the "Curveballs" section.
4. When the timer ends, stop editing `DESIGN.md`. Then fill in `ANSWER.md` as a review of a recording:
   what you skipped, where you hand-waved, what you would say differently.

## What you have

| Path | What it is |
|---|---|
| `inputs/prompt.md` | the interviewer's prompt and the facts you may ask for |
| `inputs/curveballs.md` | the minute-30 follow-ups (do not open early) |
| `DESIGN.md` | the whiteboard template |
| `ANSWER.md` | your self-review |

## Acceptance criteria (what the grader checks)

- Graded by rubric only: `grade.sh` prints a completeness report and `GRADE_TESTS {"passed": 0, "total": 0}`;
  the rubric's automated row does not apply.
- The method is visible: requirements and non-goals, estimates, API, data model, design, deep dives.
- The engine (Temporal) is separated from the product-facing primitives and API.
- Tenancy, quotas, versioning of definitions and observability are handled.
- Every curveball gets a mechanism.

## How to run

```bash
make setup       # prints the rules
make test        # completeness report
# from workbooks/ in Claude Code: /grade backend/x-1
```
