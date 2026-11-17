# audit/x-1 - Azure Function cannot reach Gemini: Workload Identity Federation impersonation denied

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 7 add-on (Mon: Workload Identity Federation from Azure to Google Cloud)

## Symptoms (as reported)

> From: R. Alvarez (ControlPilot lead) - Tue 2026-11-10 07:50
>
> The nightly CM-03 job moved from the old service-account key to keyless federation yesterday
> (security finding SEC-2291: no long-lived Google keys on Azure). The Function now fails at 02:00
> with `Unable to acquire impersonated credentials ... iam.serviceAccounts.getAccessToken denied`.
> The Azure side looks fine. The cloud team thinks the token audience is wrong: the credential
> config says `//iam.googleapis.com/...` but the token says `api://...`, and those clearly do not
> match. Someone also suggested granting the pool `roles/owner` "just to get it running tonight".
> Please fix it properly before tonight's run.

ControlPilot runs as an Azure Function with the user-assigned managed identity
`id-controlpilot-func`. It gets an Entra token from Azure IMDS, exchanges it at Google STS through the
workload identity pool `azure-mfh` / provider `entra-prod`, impersonates the service account
`controlpilot-gemini@mfh-controlpilot-prod.iam.gserviceaccount.com` and calls Gemini on Gemini
Enterprise Agent Platform (formerly Vertex AI). `wifsim/sim.py` is a local, faithful simulator of
that path that reads the same configuration files (read its docstring; the simulator is not the bug).

## What you have

| Path | What it is |
|---|---|
| `config/credential-config.json` | the external_account credential config deployed with the Function |
| `config/wif-provider.json` | the pool provider: issuer, allowed audiences, attribute mapping and condition |
| `config/sa-iam-policy.json` | IAM policy on the service account |
| `config/project-iam-policy.json` | project roles of the service account |
| `incident/` (from `make setup`) | decoded Entra token claims, `az identity show`, Function log, GCP audit log |
| `wifsim/` | the simulator (`make sim`) |

## Your task

1. Follow the call path hop by hop with the evidence and find where and why it fails. Decide whether
   the audience theory is right, with evidence.
2. Fix the configuration in `config/` with least privilege: only this Function's identity may
   impersonate the service account. No keys, no wider grants, no loosening of the provider.
3. `make sim` and `make test`; write `ANSWER.md` (root cause with the claims and log lines, the fix,
   why the alternatives people suggested are wrong, and what you would add for production).

## Acceptance criteria (what the grader checks)

- The Function's token reaches Gemini through the simulator.
- Another managed identity in the same tenant, a token from another tenant and a token with another
  audience are all denied.
- No `allUsers`, `allAuthenticatedUsers`, whole-pool or tenant-wide principalSet, `roles/owner`,
  `roles/editor` or token-creator grants; exactly one principal holds `roles/iam.workloadIdentityUser`;
  no service account key; audiences, issuer and the tenant condition unchanged.
- `ANSWER.md` names the root cause with evidence and rules the audience theory out.

## How to run

```bash
make setup     # venv + incident/
make sim       # run the call path against config/
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade audit/x-1
make clean
```
