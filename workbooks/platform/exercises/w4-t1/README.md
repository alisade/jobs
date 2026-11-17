# platform/w4-t1 - AppDatabase XRs never become Ready

**Type:** troubleshooting | **Estimate:** 1-1.5 hours | **Study plan:** Week 4 (Crossplane v2, providers, compositions)

## Scenario

Tessellate (fictional) offers developers a namespaced `AppDatabase` (Crossplane v2: namespaced XRs,
no claims) that composes Cloud SQL managed resources from the Upbound GCP SQL provider. Yesterday's
platform release moved from v1 claims to v2 namespaced XRs and the namespaced MR API groups
(`sql.gcp.m.upbound.io`). Since then every team's database is `Ready=False` and nothing exists in Cloud
SQL. A colleague wants to add a JSON key secret because the provider logged a token warning. RDM
onboards next week, so the fix must work for a new team namespace without platform tickets.

## What you have

| Path | What it is |
|---|---|
| `evidence/PAGE.txt`, `evidence/kubectl.txt` | the thread, trace, describe, provider config listing, provider logs |
| `platform/` | XRD, Composition (function-patch-and-transform), provider and its config |
| `teams/` | the teams' XRs |
| `tools/xpsim.py` | renders each XR through the Composition and simulates the provider's config lookup (read the docstring for the model it implements) |

## Your task

1. `make reconcile`: which resources are not Ready, and what are they waiting for?
2. Explain why the lookup fails although a config named `default` exists. Rule out the token theory.
3. Fix it in `platform/` (not per team), so a new team namespace works with no extra objects, keeping
   Workload Identity (no keys) and every Composition mapping.
4. `ANSWER.md`: root cause, evidence, fix, how you would catch this before a release.

## Acceptance criteria (what the grader checks)

- All XRs in `teams/` and a new `team-rdm` XR become Ready with your `platform/`.
- Tier and version mapping, deletion protection, `deletionPolicy: Orphan` and the connection secret name
  are unchanged.
- The XRD stays namespaced with no claim names, the Composition stays in Pipeline mode, the shared
  config keeps `InjectedIdentity` credentials and no key secret appears.
- `ANSWER.md` explains the cause with evidence.

## How to run

```bash
make setup
make reconcile
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade platform/w4-t1
make clean
```

## What to submit

Your changes in `platform/` and `ANSWER.md`.
