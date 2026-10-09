"""Build the incident/ evidence bundle for INC0049213 (run by `make setup`).

The deployed PROD definitions are produced by actually rendering the current workspace/ with
deploy/render.py, so the evidence reflects whatever parameter.yml says right now.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "deploy"))
import render  # noqa: E402

INC = ROOT / "incident"
TARGETS = json.loads((ROOT / "deploy" / "targets.json").read_text())


def w(rel: str, text: str) -> None:
    p = INC / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def meta_binding(nb_text: str) -> dict:
    lines = []
    in_meta = False
    for line in nb_text.splitlines():
        if line == "# META" or line.startswith("# META "):
            in_meta = True
            lines.append(line[len("# META"):].lstrip(" ") if len(line) > 6 else "")
        elif in_meta:
            break
    return json.loads("\n".join(lines))["dependencies"]["lakehouse"]


def main() -> None:
    if INC.exists():
        shutil.rmtree(INC)
    INC.mkdir()

    # 1. Genuine render of what Tuesday's release deployed to PROD.
    tmp = INC / ".render-tmp"
    log = render.render(ROOT / "workspace", "PROD", TARGETS, tmp)
    deployed = INC / "deployed-PROD"
    deployed.mkdir()
    for item in ("Load Gold Sales.Notebook", "nb_load_silver.Notebook", "Daily Sales.DataPipeline"):
        shutil.copytree(tmp / item, deployed / item)
    shutil.rmtree(tmp)

    gold = meta_binding((deployed / "Load Gold Sales.Notebook" / "notebook-content.py").read_text())
    silver = meta_binding((deployed / "nb_load_silver.Notebook" / "notebook-content.py").read_text())
    gws, glh = gold["default_lakehouse_workspace_id"], gold["default_lakehouse"]
    known = [k["id"] for k in gold.get("known_lakehouses", [])]
    slh_for_gold = next((k for k in known if k != glh), known[0] if known else glh)

    # 2. fabric-cicd release log (GitHub Actions job output).
    rel_lines = [
        "2026-10-06T14:09:51Z ##[group]Run python deploy/deploy.py --env PROD",
        "2026-10-06T14:09:53Z [info] Parameter file validation: parameter.yml is valid",
        "2026-10-06T14:09:53Z [info] Target workspace: Contoso Retail Sales (9a7e3b12-44c0-4f6e-b1d8-6c2a5f09e8d4), environment PROD",
        "2026-10-06T14:09:54Z [info] Item types in scope: Lakehouse, Notebook, DataPipeline",
    ]
    for entry in log:
        rel_lines.append(f"2026-10-06T14:09:55Z [debug] {entry}")
    rel_lines += [
        "2026-10-06T14:09:58Z [info] Publishing Lakehouse 'lh_gold'",
        "2026-10-06T14:10:00Z [info] Publishing Lakehouse 'lh_silver'",
        "2026-10-06T14:10:03Z [info] Publishing Notebook 'nb_load_silver'",
        "2026-10-06T14:10:07Z [info] Publishing Notebook 'Load Gold Sales'",
        "2026-10-06T14:10:09Z [info] Unpublishing orphan Notebook 'nb_load_gold'",
        "2026-10-06T14:10:12Z [info] Publishing DataPipeline 'Daily Sales'",
        "2026-10-06T14:10:15Z [info] Published 5 item(s), unpublished 1 orphan item(s)",
        "2026-10-06T14:10:15Z ##[endgroup]",
        "2026-10-06T14:10:15Z Job 'deploy-prod' completed with result: success",
    ]
    w("release-PROD-2026-10-06.log", "\n".join(rel_lines) + "\n")

    # 3. Monitoring hub export: everything green.
    runs = ["Item name,Item type,Workspace,Status,Start time (UTC),Duration,Submitted by,Job instance id"]
    days = [("2026-10-05", "06:00:04", "6m 41s"), ("2026-10-06", "06:00:03", "19m 12s"),
            ("2026-10-07", "06:00:05", "6m 55s"), ("2026-10-08", "06:00:04", "6m 38s"),
            ("2026-10-09", "06:00:05", "6m 47s")]
    for i, (d, t, dur) in enumerate(days):
        runs.append(f"Daily Sales,Pipeline,Contoso Retail Sales,Succeeded,{d} {t},{dur},svc-fabric-sched@contoso.com,8c41{i}a7e-55d0-4b8e-9e1a-2f0c6d3b7a9{i}")
        runs.append(f"nb_load_silver,Notebook,Contoso Retail Sales,Succeeded,{d} {t[:-2]}31,2m 58s,svc-fabric-sched@contoso.com,3f7{i}c2d1-0a9e-4c6b-8f21-7d5e9a1b3c4{i}")
        nb = "nb_load_gold" if d <= "2026-10-06" else "Load Gold Sales"
        runs.append(f"{nb},Notebook,Contoso Retail Sales,Succeeded,{d} 06:03:{40 + i},3m 21s,svc-fabric-sched@contoso.com,b2e{i}9f40-6c1d-4a8e-b5f3-0d9c7e2a4b6{i}")
    w("monitoring-hub-export.csv", "\n".join(runs) + "\n")

    # 4. Spark driver log of Thursday's PROD gold run (the binding is read from the deployed definition).
    prod_ws = TARGETS["PROD"]["workspace_id"]
    driver = f"""2026-10-08 06:03:44,102 INFO SparkContext [Thread-4]: Running Spark version 3.5.1.5.4.20250519.1
2026-10-08 06:03:44,377 INFO SparkContext [Thread-4]: Submitted application: Load Gold Sales (Notebook) - workspace {prod_ws}
2026-10-08 06:03:46,011 INFO TokenLibrary [Thread-4]: Acquired OneLake token for user svc-fabric-sched@contoso.com
2026-10-08 06:03:47,520 INFO NotebookUtils [Thread-4]: Default lakehouse resolved: name=lh_gold id={glh} workspace={gws}
2026-10-08 06:03:47,522 INFO HiveCatalog [Thread-4]: Default database set to lh_gold (abfss://{gws}@onelake.dfs.fabric.microsoft.com/{glh}/Tables)
2026-10-08 06:03:52,846 INFO DeltaLog [Thread-23]: Loading version 412 of abfss://{gws}@onelake.dfs.fabric.microsoft.com/{slh_for_gold}/Tables/sales_clean
2026-10-08 06:03:58,190 INFO FileSourceStrategy [Thread-23]: Pushed Filters: IsNotNull(order_date),EqualTo(order_date,2026-10-08)
2026-10-08 06:04:31,774 WARN TaskSetManager [task-result-getter-2]: Lost task 14.0 in stage 7.0 (TID 211) (vm-7c1e3a0b executor 3): ExecutorLostFailure (executor 3 exited caused by one of the running tasks) Reason: Container from a bad node: container_1728367413_0004_01_000004 on host: vm-7c1e3a0b. Exit status: 143.
2026-10-08 06:04:31,790 INFO TaskSetManager [dispatcher-event-loop-1]: Starting task 14.1 in stage 7.0 (TID 219) (vm-2d9f4b61, executor 5, partition 14, PROCESS_LOCAL)
2026-10-08 06:04:44,005 WARN GarbageCollectionMonitor [driver-heartbeater]: Driver GC time 18.2% of last 60s (threshold 15%)
2026-10-08 06:05:09,617 INFO TaskSetManager [task-result-getter-0]: Finished task 14.1 in stage 7.0 (TID 219) in 25611 ms on vm-2d9f4b61 (executor 5) (64/64)
2026-10-08 06:05:12,330 INFO OptimisticTransaction [Thread-23]: [tableId=4e1b7c90,txnId=a6d2f1e8] Committed delta #388 to abfss://{gws}@onelake.dfs.fabric.microsoft.com/{glh}/Tables/sales_daily/_delta_log
2026-10-08 06:05:12,911 INFO VOrder [Thread-23]: V-Order applied to 4 file(s), 12.4 MiB
2026-10-08 06:05:13,402 INFO NotebookOutput [Thread-4]: gold.sales_daily rows written for 2026-10-08: 1874
2026-10-08 06:05:13,950 INFO SparkContext [Thread-4]: Successfully stopped SparkContext
2026-10-08 06:05:14,001 INFO NotebookRunner [main]: Notebook run finished with status Succeeded
"""
    w("spark-driver-Load-Gold-Sales-PROD-2026-10-08.log", driver)

    # 5. Delta history of sales_daily in both lakehouses (DESCRIBE HISTORY, trimmed).
    def hist(rows):
        return "version | timestamp           | operation | operationParameters                                  | operationMetrics\n" + "\n".join(rows) + "\n"
    prod_rows = [
        "391     | 2026-10-06 06:05:02 | WRITE     | mode=Overwrite, predicate=[\"(order_date = '2026-10-06')\"] | numOutputRows=1912",
        "390     | 2026-10-05 06:04:58 | WRITE     | mode=Overwrite, predicate=[\"(order_date = '2026-10-05')\"] | numOutputRows=1766",
        "389     | 2026-10-04 06:05:10 | WRITE     | mode=Overwrite, predicate=[\"(order_date = '2026-10-04')\"] | numOutputRows=2240",
    ]
    dev_rows = [
        "389     | 2026-10-09 06:05:21 | WRITE     | mode=Overwrite, predicate=[\"(order_date = '2026-10-09')\"] | numOutputRows=1903",
        "388     | 2026-10-08 06:05:12 | WRITE     | mode=Overwrite, predicate=[\"(order_date = '2026-10-08')\"] | numOutputRows=1874",
        "387     | 2026-10-07 06:05:17 | WRITE     | mode=Overwrite, predicate=[\"(order_date = '2026-10-07')\"] | numOutputRows=1890",
        "386     | 2026-10-07 04:31:40 | WRITE     | mode=Overwrite, predicate=[\"(order_date = '2026-10-06')\"] | numOutputRows=212",
        "385     | 2026-10-06 04:31:36 | WRITE     | mode=Overwrite, predicate=[\"(order_date = '2026-10-05')\"] | numOutputRows=208",
    ]
    w("delta-history/PROD_lh_gold.sales_daily.txt", "-- Contoso Retail Sales / lh_gold / sales_daily, run 2026-10-09 09:12 UTC\n" + hist(prod_rows))
    w("delta-history/DEV_lh_gold.sales_daily.txt",
      "-- Contoso Retail Sales [DEV] / lh_gold / sales_daily, run 2026-10-09 09:14 UTC\n"
      "-- DEV schedule runs 04:30 UTC against the 200-row sample feed\n" + hist(dev_rows))

    # 6. Item inventories (Fabric REST: GET /v1/workspaces/{id}/items).
    for env in ("DEV", "PROD"):
        t = TARGETS[env]
        value = []
        for itype, items in t["items"].items():
            for name, gid in items.items():
                value.append({"id": gid, "type": itype, "displayName": name, "workspaceId": t["workspace_id"]})
        w(f"items-{env}.json", json.dumps({"value": value}, indent=2) + "\n")

    # 7. Git history of the release.
    w("git-log.txt", """commit 7be1c09 (tag: release-2026.10.06)
Merge: 41d0a2e 9f3c6b1
Author: Priya Natarajan <priya.natarajan@contoso.com>
Date:   Tue Oct 6 13:58:12 2026 +0000

    Merge PR #412: Rename notebooks to display-name convention

commit 9f3c6b1
Author: Dan Okafor <dan.okafor@contoso.com>
Date:   Mon Oct 5 16:21:40 2026 +0000

    Rename nb_load_gold -> Load Gold Sales; fix pipeline notebookId parameter

    PPE dry run failed: $items.Notebook.nb_load_gold.$id does not resolve. Updated the
    key_value_replace entry to the new display name.

 workspace/{nb_load_gold.Notebook => Load Gold Sales.Notebook}/.platform             | 2 +-
 workspace/{nb_load_gold.Notebook => Load Gold Sales.Notebook}/notebook-content.py   | 0
 workspace/parameter.yml                                                               | 2 +-
 3 files changed, 2 insertions(+), 2 deletions(-)
""")

    # 8. Chat thread (contains a red herring).
    w("teams-thread.txt", """#data-platform  Thu 2026-10-09
[08:41] Mei (Sales Ops): Store dashboard still shows Tuesday as the last day. Wed/Thu missing. Pipeline says Succeeded??
[08:47] Dan: Tuesday's 06:00 run took 19 min, capacity was throttled (F64 at 104% smoothed). Probably that again.
[08:52] Dan: Also seeing ExecutorLostFailure + GC warnings in the gold notebook driver log. Maybe the writes are failing silently?
[09:03] Priya: The capacity throttling was Tuesday morning only, Capacity Metrics app is clean since. Delta history on PROD lh_gold says last commit Tuesday 06:05.
[09:05] Priya: Assigning INC0049213 to platform on-call.
""")

    w("README.txt", """INC0049213 evidence bundle (generated by make setup)

release-PROD-2026-10-06.log           GitHub Actions output of deploy/deploy.py --env PROD (fabric-cicd)
deployed-PROD/                        item definitions as published to PROD by that release
monitoring-hub-export.csv             Monitoring hub, PROD workspace, last 5 days
spark-driver-*.log                    Spark driver log of Thursday's PROD gold notebook run
delta-history/                        DESCRIBE HISTORY of sales_daily in the PROD and DEV lh_gold
items-DEV.json / items-PROD.json      Fabric REST List Items for both workspaces
git-log.txt                           what changed in the release
teams-thread.txt                      the conversation so far
""")
    print(f"incident bundle written to {INC.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
