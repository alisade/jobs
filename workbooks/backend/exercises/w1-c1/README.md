# backend/w1-c1 - Whiteboard write-up: the Keystone platform layer

**Type:** design | **Estimate:** 2-3 hours | **Study plan:** Week 1 (Mon: whiteboard method; Tue: service boundaries and multi-tenancy; Wed: consistency and ADRs; Thu: CRM domain)

## Scenario

Lumenfold (fictional, an enterprise data and AI platform company, 9,000 employees) runs its sales,
partner and renewals apps on a third-party CRM. The contract renews in 20 months and the CRM's
automation (flows, triggers, validation rules) has become the place where business logic goes to hide.
Leadership approved Keystone: a platform layer Lumenfold builds and owns, on which product teams
rebuild those apps and on which a new generation of agentic apps (a sales assistant, a renewals agent)
will run.

You joined the Keystone team this week. Tomorrow is the first architecture session with Priya
Natarajan (staff engineer) and the product leads. Priya asked for a written whiteboard: the design
you would draw, with the reasoning, so the session can argue about decisions instead of boxes.

## What you have

| Path | What it is |
|---|---|
| `inputs/brief.md` | the program brief: goals, users, constraints, what "platform" means here |
| `inputs/crm-inventory.md` | objects, custom fields, automation and integrations in the current CRM |
| `inputs/volumes.md` | record counts, growth, traffic, latency and availability targets |
| `DESIGN.md` | the template you fill in (the main deliverable) |
| `adr/0001-tenancy-model.md` | ADR template: how tenants are isolated |
| `adr/0002-service-integration.md` | ADR template: how services talk to each other |
| `ANSWER.md` | approach, key decisions, trade-offs |

## Your task

1. Fill in every section of `DESIGN.md`. Follow the interview method: requirements and non-goals,
   estimates, core entities, API surface, high-level design, then two deep dives on the riskiest parts.
2. Draw the service boundaries around data ownership and business capability. Every table has exactly
   one owning service. Diagrams in ```text or ```mermaid blocks.
3. Decide, for each capability, whether it is exposed as a synchronous API, an event, a workflow or an
   agent tool, and say why.
4. Write the two ADRs (context, options with real trade-offs, decision, consequences).
5. Summarize in `ANSWER.md`.

Write as if the document will be reviewed by senior engineers who will push on every number and every
boundary. Say what you would ask the business before committing where the inputs are ambiguous.

## Acceptance criteria (what the grader checks)

- Graded by rubric only: `grade.sh` prints a completeness report and `GRADE_TESTS {"passed": 0, "total": 0}`;
  the rubric's automated row does not apply.
- Estimates are computed from `inputs/volumes.md` and used to justify choices (indexes, partitioning,
  fan-out, caching, pool sizes).
- Boundaries: one owner per table, integration through APIs and events, no shared tables.
- Hidden CRM logic from `inputs/crm-inventory.md` has a named new home (service code, constraint,
  workflow, or explicitly dropped).
- Agentic apps act on behalf of a user with no more access than that user, and risky writes go through
  a workflow approval.
- Both ADRs present at least two serious options and a decision with consequences.

## How to run

```bash
make test        # completeness report: which sections are still empty
# from workbooks/ in Claude Code: /grade backend/w1-c1
```
