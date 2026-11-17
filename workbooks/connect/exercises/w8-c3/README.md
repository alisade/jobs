# connect/w8-c3 - CI/CD and release management for the Connect platform

**Type:** design | **Estimate:** 2 hours | **Study plan:** Week 8 (Mon: CI/CD across environments; Wed: testing flows, blue/green; Thu: monitoring and HA)

## Scenario

Larkspur Financial Group's help desk platform has five Connect instances (sandbox, dev, test,
prod, and a us-west-2 DR replica). Flows are built in the dev console by the Pune and Monterrey
teams and moved with an export script; Lambdas reach prod by hand; prompts, Contact Lens rules
and evaluation forms are clicked into each instance. On 2026-10-06 a green pipeline shipped a
prod flow pointing at the dev Lex alias (connect/w8-t1). The CIO wants weekly releases with a
real rollback, and the offshore teams able to ship without a Boston engineer awake.

## What you have

| Path | What it is |
|---|---|
| `inputs/current-state.md` | environments, what is code today, pain points, verified platform facts |
| `inputs/constraints.md` | tooling, approvals, cadence, freeze, audit and offshore constraints |
| `DESIGN.md` | the design document template you fill in (the deliverable) |

## Your task

1. Fill in every section of `DESIGN.md`, including a GitHub Actions workflow sketch (YAML) for the
   flow release path and a resource-by-resource "managed as code" table.
2. Be precise about what CloudFormation/CDK and Terraform cover for Connect, and about what can and
   cannot be versioned or aliased (flows vs modules vs Lambdas vs Lex).
3. Summarize your key decisions in `ANSWER.md`.

## Acceptance criteria (what the grader checks)

There are no automated tests (`grade.sh` prints a completeness report and `GRADE_TESTS
{"passed": 0, "total": 0}`). The rubric carries all 100 points: IaC coverage accuracy, promotion
and reference handling, pipeline and testing, release and rollback, monitoring and verification,
governance and the offshore model, and communication.

## How to run

```bash
make setup      # nothing to install
make test       # completeness report: which sections are still empty
# then from workbooks/ in Claude Code: /grade connect/w8-c3
```
