# ms/w3-t1: PROD gold table stale, pipeline green

Type: troubleshooting. Estimate: 1.5-2.5 h. Exam: DP-700 - Implement and manage an analytics solution (30-35%): lifecycle management (git, deployment); Monitor and optimize (30-35%): identify and resolve errors.

## Scenario

Contoso Retail runs its sales analytics in Microsoft Fabric. The DEV workspace `Contoso Retail Sales [DEV]`
is connected to git (this folder's `workspace/` is that repo directory). Releases to PPE and PROD are done by
GitHub Actions running `deploy/deploy.py`, which uses the
[fabric-cicd](https://microsoft.github.io/fabric-cicd/) Python library and `workspace/parameter.yml` to swap
environment-specific GUIDs at publish time.

Pager, Friday 2026-10-09 08:55 UTC, INC0049213 (Sev 3):

> Store sales dashboard shows Tuesday 2026-10-06 as the latest day. Wednesday and Thursday are missing in PROD.
> The `Daily Sales` pipeline and both notebooks show **Succeeded** every morning in the Monitoring hub.
> There was a release on Tuesday afternoon. People in the channel think it is capacity throttling again.

You do not have access to Fabric for this exercise. You have the repo plus an evidence bundle that `make setup`
generates into `incident/` (release log, the definitions as deployed to PROD, Monitoring hub export, Spark driver
log, Delta table history, item inventories, git log, chat thread). `make render ENV=PROD` dry-runs the release
locally with `deploy/render.py`, an offline reimplementation of the fabric-cicd parameterization subset this
repo uses (see its docstring; the behaviour it mirrors is quoted from the fabric-cicd docs).

## Your task

1. Find the root cause and prove it with evidence from `incident/` and a local dry run.
2. Fix it in the repo so PPE and PROD releases bind every notebook and pipeline to their own workspace, and so
   the same class of mistake cannot silently happen again on the next rename.
3. Implement the release guard `deploy/check_bindings.py` (contract below) so a release fails loudly instead
   of publishing a definition that points at another environment.
4. Write `ANSWER.md`, including what has to happen to the PROD and DEV data that was affected.

### Guard

`find_leaks(rendered: Path, env: str, targets: dict) -> list[str]`: scan every file under `rendered`
except `.platform`, find GUIDs (case-insensitive), and report each GUID that `deploy/targets.json` attributes to
an environment other than `env` (any other environment, including another target such as PPE inside a PROD
render). One string per (file, GUID): `"<relative path>: <guid> (<ENV> <label>)"`, for example
`Load Gold Sales.Notebook/notebook-content.py: 6e0d...e5f6 (DEV Lakehouse lh_gold)`. GUIDs that are not in
`targets.json` are ignored. `main()` prints `LEAK <line>` per leak and exits 1 when there is any leak, else 0.

## Acceptance criteria

- `make render ENV=PROD` and `ENV=PPE`: no file references a GUID from another environment; the gold notebook's
  default lakehouse, its workspace and its known lakehouses all point at the target environment.
- The silver notebook and the `Daily Sales` pipeline still render correctly (no regression).
- DEV source in `workspace/` keeps DEV GUIDs and contains no PPE/PROD GUIDs (the fix lives in parameterization,
  not in hand-edited definitions), and a DEV render is a no-op.
- The fix still works if the gold notebook is renamed again.
- `deploy/check_bindings.py` meets the Guard contract.
- `ANSWER.md` names the root cause with evidence and explains why everything looked green.

## How to run

```
make setup              # uv sync + generate incident/
make test               # visible tests
make render ENV=PROD    # dry-run release into incident/render/PROD
make guard ENV=PROD     # dry-run + guard
make clean
```

## What to submit

Your changes under `workspace/` and `deploy/`, and `ANSWER.md` (Approach, Root cause with evidence, Fix and how
you verified it, Trade-offs / production). Then run `/grade ms/w3-t1` from the workbooks folder.

## Study guide links

- [Week 3 Mon - Workspace settings and lifecycle](../../../../microsoft-adf-powerapps-study-plan.html#week3)
- [Week 3 Thu - Identify and resolve errors](../../../../microsoft-adf-powerapps-study-plan.html#week3)
- [Fabric git integration: source code format](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/source-code-format)
- [Deployment pipelines: deployment rules](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/create-rules)
- [fabric-cicd parameterization](https://microsoft.github.io/fabric-cicd/latest/how_to/parameterization/)
- [Monitoring hub](https://learn.microsoft.com/en-us/fabric/admin/monitoring-hub)
- [OneLake URIs and abfss paths](https://learn.microsoft.com/en-us/fabric/onelake/onelake-access-api)
