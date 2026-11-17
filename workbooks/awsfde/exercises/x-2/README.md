# awsfde/x-2 - From three one-off fixes to a reusable tenant-isolation kit

**Type:** design (optional add-on) | **Estimate:** 2-3 hours | **Study plan:** Week 7 add-on (Fri: FDE, one-off fix to reusable pattern); Week 4 (identity, ABAC and LeadingKeys); Week 3 (metadata filters); Week 6 (embedding backend)

## Scenario

Three customer engagements ended with three one-off tenant-isolation fixes: a Knowledge Base
Retrieve fallback that dropped the tenant filter, a tool Lambda that read the tenant from its
arguments, and an embed URL cached at the edge. About fourteen teams build on the platform in
TypeScript and Python, on a two-week cadence, and every change waits a week for AppSec review.
Design the kit that makes the next incident of this kind structurally hard rather than a matter
of each team remembering.

## What you have

| Path | What it is |
|---|---|
| `inputs/engagement-1-delta-outfitters.md` | KB results from another tenant |
| `inputs/engagement-2-brightline-health.md` | tool read the tenant from its arguments |
| `inputs/engagement-3-corvid-logistics.md` | embed URL served from the CDN cache |
| `inputs/constraints.md` | teams, languages, platform, cadence, review process |
| `DESIGN.md` | the design template (edit this) |
| `ANSWER.md` | short summary of your design and trade-offs (edit this) |

## Your task

1. Name the common failure pattern behind the three incidents.
2. Design the kit: a tenant-context library, a CDK construct with ABAC and `LeadingKeys`, a
   Retrieve wrapper, response and CDN defaults, an attack test kit, and a runbook.
3. Sketch the APIs in TypeScript and Python, plus a short CDK usage example.
4. Plan adoption, the evidence that it works, what not to generalize, and the FDE story you
   would tell the next customer.

## Acceptance criteria (rubric)

- The shared cause is diagnosed, not just the three incidents listed.
- Each incident is mapped to at least two layers that would have stopped it, one beyond
  application code.
- The adoption plan fits the constraints and comes with measurable signals that it works.

## How to run

```bash
make setup      # nothing to install
make test       # completeness report (rubric-graded, no tests)
# from workbooks/ in Claude Code: /grade awsfde/x-2
make clean
```

## What to submit

`DESIGN.md` and `ANSWER.md`.
