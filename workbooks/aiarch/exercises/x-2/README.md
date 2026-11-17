# aiarch/x-2 - Pipeline ADR: GitLab-native vs CDK Pipelines, plus endpoint policies

**Type:** design (optional add-on) | **Estimate:** 2 hours | **Study plan:** Week 7 add-on (Week 6 Wed: CDK Pipelines and CodeConnections; Week 6 Thu: PrivateLink and endpoint policies)

## Scenario

Lighthouse deploys today with GitLab CI running `cdk deploy` per environment through OIDC roles.
It works, but the stakeholders now pull in different directions. Security wants deploys executed
inside AWS with a mandatory, named approver before prod. Audit wants one place that answers "who
approved what went to prod, and when". Developers want results on the merge request. FinOps wants
it cheap. You write the ADR that picks between GitLab-native `cdk deploy`, CDK Pipelines sourced
from GitLab through CodeConnections, and a hybrid, and you design the VPC endpoint policies for
the agent's private networking, including callers that present an OAuth bearer token.

## What you have

| Path | What it is |
|---|---|
| `inputs/requirements.md` | team, accounts, stakeholder positions, cost and networking facts |
| `DESIGN.md` | the ADR template (edit this) |
| `ANSWER.md` | short summary of your decision and trade-offs (edit this) |

## Your task

1. Compare the three delivery options against the stated constraints: release flow, approval
   point, audit trail, credentials, cost and effort.
2. Decide, and say what you give up.
3. Draw the release flow from merge request to the prod endpoint: build once, image digest
   promotion, approval, change window and rollback.
4. Sketch the endpoint policies for `bedrock-runtime` and `bedrock-agentcore`, including the
   bearer-token case, and explain how they interact with the `aws:SourceVpce` SCP.

## Acceptance criteria (rubric)

- Options analysed fairly, with no strawmen; a decision tied to the constraints.
- A readable release flow with digest promotion, a named approver and rollback.
- Endpoint policies scoped to the org and actions; OAuth calls handled correctly with
  `Principal "*"` plus non-principal conditions, and why IAM principal conditions cannot apply.
- Consequences and follow-ups, including a test plan for the policies.

## How to run

```bash
make setup      # nothing to install
make test       # completeness report (rubric-graded, no tests)
# from workbooks/ in Claude Code: /grade aiarch/x-2
make clean
```

## What to submit

`DESIGN.md` and `ANSWER.md`.
