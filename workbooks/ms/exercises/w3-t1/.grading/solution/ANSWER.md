# ANSWER: ms/w3-t1 PROD gold table stale, pipeline green

## Approach
Started from the data, not the runs. `incident/delta-history/PROD_lh_gold.sales_daily.txt` shows the last commit
on 2026-10-06 06:05 (version 391), so nothing has written PROD gold since Tuesday's morning run, although the
Monitoring hub shows the gold notebook Succeeded on Wed/Thu/Fri. So the notebook ran and wrote somewhere else.

The Thursday driver log shows where:

    Default lakehouse resolved: name=lh_gold id=6e0d8f4a-... workspace=2f1c6a0e-8d3b-...
    Committed delta #388 to abfss://2f1c6a0e-8d3b-4c55-9a71-0b6de4f3a210@onelake.dfs.fabric.microsoft.com/6e0d8f4a-.../Tables/sales_daily

`items-DEV.json` maps 2f1c6a0e... to the DEV workspace and 6e0d8f4a... to DEV lh_gold. DEV history has versions
387-389 at 06:05 on Wed/Thu/Fri with ~1,900 rows (PROD volumes), next to DEV's own 04:31 runs with ~200 rows.
The PROD schedule is writing into DEV. It reads DEV silver too (`known_lakehouses` 1a2b3c4d... in the log).

Ruled out: capacity throttling (Tuesday 06:00 only, Capacity Metrics clean since, and throttling delays jobs, it
does not redirect writes); ExecutorLostFailure/GC warnings (task 14.1 retried and finished 64/64, commit succeeded).

## Root cause
PR #412 renamed the notebook `nb_load_gold` to `Load Gold Sales`. In `workspace/parameter.yml` the three
`find_replace` entries that swap the DEV workspace id and the DEV lakehouse ids in notebook definitions are
filtered with `item_name: ["nb_load_silver", "nb_load_gold"]` / `item_name: "nb_load_gold"`. fabric-cicd: "If
at least one filter value does not match, the replacement will be skipped for that file", and a literal
find_value that matches nothing is not an error. So the release silently skipped the gold notebook and published
it with its DEV binding. The release log shows only two find_replace lines, both for nb_load_silver.
The pipeline entry was fixed in the same PR only because `$items.Notebook.nb_load_gold.$id` failed validation
loudly; the item_name filter fails silently.

Why green: the default lakehouse is metadata, not a connection; the schedule runs as svc-fabric-sched, which is
a member of both workspaces, so the cross-workspace OneLake read/write succeeds.

`make render ENV=PROD` before the fix reproduces it: `Load Gold Sales.Notebook/notebook-content.py` keeps
`default_lakehouse_workspace_id: 2f1c6a0e...`.

## Fix
- `parameter.yml`: removed the brittle `item_name` filters; entries are filtered by `item_type: "Notebook"` only
  (the find_values are DEV GUIDs, so matching every notebook is exactly what we want). Rendering PROD and PPE now
  rewrites the gold binding and known lakehouses; DEV render is a no-op.
- `deploy/check_bindings.py`: implemented the guard. `make guard ENV=PROD` prints `0 cross-environment
  reference(s)`; on the old parameter.yml it prints 3 LEAK lines (DEV workspace, lh_gold, lh_silver in the gold notebook) and exits 1. Wire it into `release-fabric.yml`
  between a dry-run render and `deploy.py`.
- Data: re-run the PROD gold notebook for 2026-10-07, 10-08 and 10-09 (it is replaceWhere by order_date, so
  idempotent) after redeploying. In DEV, delete or overwrite the order_date partitions 2026-10-07..09 that came
  from PROD (or restore DEV sales_daily to version 386), and check whether PROD data in DEV breaches any data
  handling rule (it is real sales data in a dev workspace).

## Trade-offs / what I would do in production
- Do not let the scheduler identity have write access to DEV (separate service principals per environment);
  the cross-env write would then have failed loudly.
- Freshness alerting on the gold table (max order_date) rather than relying on run status.
- Alternatives: Fabric deployment pipelines with deployment rules for the default lakehouse, or setting the
  lakehouse at run time (notebook parameters + `%%configure` / abfss paths built from `notebookutils` context).
  Keep one mechanism, not two.
