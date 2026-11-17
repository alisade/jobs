# platform/x-2 - Chart 3.0 reached every cluster at once

**Type:** troubleshooting (optional, add-on week) | **Estimate:** 1.5-2 hours | **Study plan:** Week 4 (Helm and ArgoCD at scale); add-on week 7

## Scenario

Tessellate runs `riq-api` on four GKE clusters through two Argo CD ApplicationSets: a canary wave
(dev-1, stg-1) that gets new chart versions first, and a stable wave (everything else). On
2026-11-10 at 14:40 Dana K. bumped the canary set to chart 3.0.0, a breaking release, planning a
48-hour soak before the prod values change and the stable bump.

At 15:11 Priya N. was paged: RIQ API 5xx on prod-blue and prod-green at the same time, pods
CrashLooping on `config: required key database.dsn not set`. Priya disabled automated sync and rolled
both prod apps back to 2.4.1. The channel's theory is that the selfHeal change from last week pulled
3.0.0 into prod. Dana wants the real root cause before automated sync is turned back on.

## What you have

| Path | What it is |
|---|---|
| `evidence/PAGE.txt` | the page and the incident channel |
| `evidence/argocd-app-history.txt` | `argocd app history` for the apps, and the live source of prod-blue |
| `evidence/argocd-events.log` | controller events around the incident |
| `evidence/git-log-platform-argocd.txt` | history of the ApplicationSets |
| `evidence/chart-release-3.0.0.md` | release notes of the chart |
| `argocd/applicationsets/*.yaml` | the two ApplicationSets (you fix these) |
| `argocd/clusters/*.yaml` | the cluster secrets with their labels |
| `charts/index.yaml` | the chart repository index as of 15:30 |
| `tools/appset_sim.py` | local stand-in for the ApplicationSet cluster generator and Helm version resolution (read its docstring) |

## Your task

1. Use `make sim` to see which chart version each cluster resolves today. Explain from the evidence
   exactly how prod moved to 3.0.0 at 15:06, and why selfHeal is or is not the cause.
2. Fix the ApplicationSets so that publishing any future chart version (a 2.x patch or minor, or a
   3.x) can never move the stable wave to a new major without a reviewed change. Keep the canary on
   3.x releases, keep Application names and value files as they are, and make sure every cluster
   (including a new cluster added later without a `wave` label) is in exactly one wave.
3. Write `ANSWER.md`: root cause with quoted evidence, the red herring, your fix, and how you would
   make chart promotion across the fleet safer (and whether automated sync goes back on).

## Acceptance criteria

- With today's index and with a future index (3.1.0, 2.5.0, pre-releases), prod stays on 2.x
  (never below 2.4.1) and canary stays on a 3.x release.
- Every cluster resolves through exactly one ApplicationSet; names and value files unchanged.
- `ANSWER.md` Root cause quotes the stable `targetRevision`, the 3.0.0 publication and says what
  selfHeal did and did not do.

## How to run

```bash
make setup
make sim                                  # what each cluster resolves today
make sim INDEX=charts/index.yaml ARGS=--json
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade platform/x-2
make clean
```

## What to submit

Your edits under `argocd/` and `ANSWER.md`.
