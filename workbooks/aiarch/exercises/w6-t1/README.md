# aiarch/w6-t1 - Prod deploy blocked by an explicit deny in an SCP

**Type:** troubleshooting | **Estimate:** 1-1.5 hours | **Study plan:** Week 6 (Wed: CDK Pipelines and bootstrap trust; Week 1 Tue: SCP evaluation)

## Symptom

The v2.6.0 prod deploy of the Lighthouse runtime stack failed and rolled back: CloudFormation
could not create a new IAM role "with an explicit deny in a service control policy". Dev
deployed fine two days earlier. Security attached a new SCP to the Workloads OU yesterday,
but it exempts the `gitlab-deploy-*` roles the pipeline uses, so on-call blames the deploy
role's permissions boundary. Read `incident/PAGE.txt` first (created by `make setup`).

## What you have

| Path | What it is |
|---|---|
| `incident/PAGE.txt`, `incident/cloudformation-events.txt` | the ticket and the stack events |
| `incident/cloudtrail-createrole.json` | the denied CreateRole call |
| `incident/assume-chain.txt` | which role makes which call in a CDK deploy |
| `incident/gitlab-deploy-prod-boundary.json` | the deploy role's boundary |
| `policies/` | the org's SCPs and RCP (from w1-c1) plus `scp-iam-change-control.json` (edit this) |
| `scpsim/`, `org/` | the evaluator and org layout from w1-c1 (work as shipped) |

## Your task

1. Find the root cause from the evidence: which principal made the denied call, and why the
   SCP's exemption does not cover it. Explain why dev worked.
2. Fix the SCP with the smallest change that keeps SEC-3110's intent: IAM changes in workload
   accounts only through CloudFormation driven by the CDK pipeline (and break-glass). The GitLab
   and CDK deploy roles themselves, developers, agent roles and roles merely named `cdk-...`
   must not change IAM.
3. Verify with `make sim` and `make test`.
4. Write `ANSWER.md`: Approach, Root cause (with evidence), Fix and verification, Trade-offs.
   Say why the boundary theory is wrong.

## Acceptance criteria (what the grader checks)

- Request decisions for the exec role, deploy roles, developers, agent roles, break-glass and
  look-alike role names; the org guardrails from w1-c1 still hold.
- No blanket `cdk-*` or `role/*` exemption; the SCP stays on Workloads.
- `ANSWER.md` names the CloudFormation execution role as the caller, with evidence.

## How to run

```bash
make setup     # evidence bundle + aiarch/.venv
make sim       # decisions for the visible requests
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade aiarch/w6-t1
make clean
```

## What to submit

`policies/scp-iam-change-control.json` and `ANSWER.md`.
