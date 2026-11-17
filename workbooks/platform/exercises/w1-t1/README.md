# platform/w1-t1 - Prod apply denied after the WIF hardening PR

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 1 (Tue service accounts and impersonation, Wed Workload Identity Federation)

## Scenario

Tessellate (fictional) applies its GCP foundation from GitHub Actions. There are no service account keys:
the workflow requests a GitHub OIDC token, exchanges it at Google STS through a Workload Identity
Federation (WIF) provider, and impersonates `tf-plan` (pull requests) or `tf-apply` (pushes to main,
running in the protected `production` environment).

Since this morning every apply on main fails. PR plans still work. InfoSec wants the
`gcp.resourceLocations` org policy enforced before the CAB window closes at 18:00 UTC, and that change is
stuck behind the broken apply. You are on call.

## What you have

| Path | What it is |
|---|---|
| `evidence/PAGE.txt` | the on-call thread, with two suggestions from colleagues |
| `evidence/actions-run-4412.log` | the failing apply job log |
| `evidence/claims/*.json` | decoded OIDC token claims of a PR plan run (4409) and the failing apply run (4412), captured by a debug step |
| `evidence/audit-logs.jsonl` | Cloud Audit Logs entries from `tsl-platform-ci` around the failure |
| `evidence/pr-388.diff` | the security PR merged this morning |
| `ci/foundation.yml` | the workflow |
| `infra/wif.tf.json` | the pool, provider, service accounts and IAM bindings (Terraform JSON syntax) |
| `tools/wifsim.py` | a local simulator of the STS exchange and the impersonation check (read its docstring) |

`make repro` replays both recorded tokens through the simulator. The simulator implements the same two
checks Google does: the provider's `attribute_condition` (STS exchange) and the
`roles/iam.workloadIdentityUser` binding on the service account (impersonation).

## Your task

1. Find which of the two steps fails and why. Use the logs and claims, not just the simulator.
2. Decide what the security PR was trying to achieve and keep that intent.
3. Fix `infra/wif.tf.json` (and only what else you must) so that the production apply works again, and
   so that only that job can impersonate `tf-apply`.
4. Write `ANSWER.md`: root cause with quoted evidence, why the two suggestions in the thread are wrong,
   the fix, and how you would stop this class of mistake reaching main again.

## Acceptance criteria (what the grader checks)

- With your config, a production-environment apply token from `tessellate/platform-foundation` gets
  `tf-apply`; tokens from a PR, a feature-branch push, a main push without the environment, the staging
  environment, another tessellate repository and a fork-owned repository do not.
- PR and branch tokens of the repository still get `tf-plan`; a fork-owned token does not.
- `tf-apply` has no pool-wide (`/*`) or repository-wide (`attribute.repository/...`) binding, the
  provider still pins the GitHub owner, and the apply job keeps `environment: production`.
- `ANSWER.md` names the root cause with evidence from at least three artifacts and rules out the red herrings.

## How to run

```bash
make setup
make repro      # replay the two recorded runs
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade platform/w1-t1
make clean
```

## What to submit

Your changes to `infra/` (and anything else you changed) and `ANSWER.md`.
