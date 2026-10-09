"""Generate the incident bundle in incident/ (run by `make setup`).

The failing run is produced by actually dry-running the CURRENT pipeline definition with
tools/simulate_run.py, so the error JSON is genuine for whatever is checked in.
"""

import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from simulate_run import simulate  # noqa: E402

INC = os.path.join(ROOT, "incident")
PIPE = os.path.join(ROOT, "pipelines", "PL_Nightly_ERP_Load.DataPipeline", "pipeline-content.json")
FAILED_RUN = "7c0a3f52-91d4-4b8e-a6f1-0e2d93b4c711"
SLOW_RUN = "e41b9d07-2c6a-4f15-8b3e-5d7a1c0f9e28"
OK_RUN = "1f9e6c3a-7b2d-4e80-9a54-c3d2e1f0a9b8"


def w(rel, content):
    path = os.path.join(INC, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        if isinstance(content, str):
            f.write(content)
        else:
            json.dump(content, f, indent=2)
            f.write("\n")


def copy_run(name, schema, table, rows, minutes, start, perf=None):
    detail = {
        "source": {"type": "AzureSqlDatabase", "region": "East US"},
        "sink": {"type": "Lakehouse", "region": "East US"},
        "status": "Succeeded",
        "start": start,
        "duration": minutes * 60,
        "usedParallelCopies": 1,
        "profile": {
            "queue": {"status": "Completed", "duration": 4},
            "transfer": {"status": "Completed", "duration": minutes * 60 - 6,
                          "details": {"readingFromSource": {"type": "AzureSqlDatabase", "workingDuration": minutes * 60 - 40, "timeToFirstByte": 31},
                                      "writingToSink": {"type": "Lakehouse", "workingDuration": 22}}},
        },
        "detailedDurations": {"queuingDuration": 4, "timeToFirstByte": 31, "transferDuration": minutes * 60 - 6},
    }
    if perf:
        detail["perfRecommendation"] = perf
    return {
        "activityName": "CopyTable",
        "activityType": "Copy",
        "iterationScope": name,
        "status": "Succeeded",
        "activityRunStart": start,
        "durationInMs": minutes * 60_000,
        "input": {"source": {"type": "AzureSqlSource", "sqlReaderQuery": f"SELECT * FROM [{schema}].[{table}] WHERE [ModifiedDate] > '2026-10-11T02:00:00'"}},
        "output": {"dataRead": rows * 212, "rowsRead": rows, "rowsCopied": rows, "copyDuration": minutes * 60,
                   "usedParallelCopies": 1, "executionDetails": [detail],
                   "effectiveIntegrationRuntime": "WorkspaceIR (East US)"},
        "error": {"errorCode": "", "message": "", "failureType": "", "target": "CopyTable", "details": ""},
    }


def main():
    if os.path.isdir(INC):
        shutil.rmtree(INC)
    os.makedirs(INC)

    failed = simulate(PIPE, run_id=FAILED_RUN, trigger_time="2026-10-13T02:00:00Z")
    w(f"runs/2026-10-13T0200Z_{FAILED_RUN}.json", failed)

    throttle_tip = [{
        "Tip": "The source Azure SQL Database was close to its DTU limit (DTU usage 96%) during the copy. "
               "Consider scaling up the source database tier or running the copy in a less busy window.",
        "ReferUrl": "https://go.microsoft.com/fwlink/?linkid=2043670",
        "RuleName": "AzureDbTierUpgradePerfRecommendRule",
    }]
    slow = {
        "runId": SLOW_RUN, "pipelineName": "PL_Nightly_ERP_Load", "status": "Succeeded", "message": "",
        "runStart": "2026-10-12T02:00:00Z", "invokedBy": {"name": "Nightly 02:00 UTC", "invokedByType": "ScheduleTrigger"},
        "pipelineVersion": "PR #405 (before PR #412)",
        "activityRuns": [
            {"activityName": "LookupTables", "activityType": "Lookup", "status": "Succeeded", "durationInMs": 8_904,
             "activityRunStart": "2026-10-12T02:00:03Z",
             "input": {"source": {"sqlReaderQuery": "SELECT load_id, schema_name, table_name, target_table, watermark_column, last_watermark FROM etl.load_control WHERE source_system = 'erp' AND is_enabled = 1"}, "firstRowOnly": False},
             "output": {"count": 4, "value": "[4 rows, truncated in export]", "effectiveIntegrationRuntime": "WorkspaceIR (East US)"}},
            {"activityName": "ForEachTable", "activityType": "ForEach", "status": "Succeeded", "durationInMs": 6_421_000,
             "activityRunStart": "2026-10-12T02:00:12Z", "output": {"iterations": 4}},
            copy_run("ForEachTable[0]", "Sales", "SalesOrderHeader", 18_220, 9, "2026-10-12T02:00:14Z"),
            copy_run("ForEachTable[1]", "Sales", "SalesOrderLine", 2_904_118, 107, "2026-10-12T02:00:14Z", throttle_tip),
            copy_run("ForEachTable[2]", "Purchasing", "PurchaseOrderHeader", 3_410, 4, "2026-10-12T02:00:14Z"),
            copy_run("ForEachTable[3]", "Production", "Product", 211, 2, "2026-10-12T02:00:14Z"),
        ],
    }
    w(f"runs/2026-10-12T0200Z_{SLOW_RUN}.json", slow)

    hub = [
        {"itemName": "PL_Nightly_ERP_Load", "runId": FAILED_RUN, "status": "Failed", "start": "2026-10-13T02:00:00Z",
         "duration": "0h 0m 11s", "invokedBy": "Schedule", "submitter": "svc-fabric-scheduler", "errorCode": "ERP_LOAD_FAILED"},
        {"itemName": "PL_Nightly_ERP_Load", "runId": SLOW_RUN, "status": "Succeeded", "start": "2026-10-12T02:00:00Z",
         "duration": "1h 47m 22s", "invokedBy": "Schedule", "submitter": "svc-fabric-scheduler", "errorCode": ""},
        {"itemName": "PL_Nightly_ERP_Load", "runId": OK_RUN, "status": "Succeeded", "start": "2026-10-11T02:00:00Z",
         "duration": "0h 41m 05s", "invokedBy": "Schedule", "submitter": "svc-fabric-scheduler", "errorCode": ""},
        {"itemName": "NB_Silver_ERP", "runId": "b7d1e2f3-0a4c-4d5e-9f6a-7b8c9d0e1f2a", "status": "Succeeded",
         "start": "2026-10-13T04:00:00Z", "duration": "0h 3m 12s", "invokedBy": "Schedule", "submitter": "svc-fabric-scheduler",
         "errorCode": "", "note": "processed 0 new bronze rows"},
    ]
    w("monitoring-hub-runs.json", hub)

    w("git-log.txt", """commit 3e9b1d7c2a4f (origin/main)
Merge: 8c1f0a2 51d7e9b
Author: Priya Raman <priya.raman@northwindtraders.example>
Date:   Mon Oct 12 16:10:44 2026 +0000

    Merge pull request #412: refactor: move control table from Azure SQL to Fabric Warehouse

    - etl.load_control now lives in WH_Control (Fabric Warehouse), deployed from the database project
    - columns renamed to the naming standard (schema_name -> source_schema, table_name -> source_table)
    - LookupTables re-pointed at WH_Control; connection re-created in the pipeline editor
    - deployed to prod workspace with the deployment pipeline at 16:22 UTC

 pipelines/PL_Nightly_ERP_Load.DataPipeline/pipeline-content.json | 31 ++++++++------
 warehouse/WH_Control/etl/Tables/load_control.sql                  | 21 ++++++++++
 2 files changed, 38 insertions(+), 14 deletions(-)

diff --git a/pipelines/PL_Nightly_ERP_Load.DataPipeline/pipeline-content.json b/pipelines/PL_Nightly_ERP_Load.DataPipeline/pipeline-content.json
@@ -9,26 +9,30 @@
         "typeProperties": {
           "source": {
-            "type": "AzureSqlSource",
+            "type": "DataWarehouseSource",
             "sqlReaderQuery": {
-              "value": "SELECT load_id, schema_name, table_name, target_table, watermark_column, last_watermark FROM etl.load_control WHERE source_system = '@{pipeline().parameters.source_system}' AND is_enabled = 1",
+              "value": "SELECT load_id, source_schema, source_table, target_table, watermark_column, last_watermark FROM etl.load_control WHERE source_system = '@{pipeline().parameters.source_system}' AND is_enabled = 1",
               "type": "Expression"
             },
             "queryTimeout": "02:00:00",
             "partitionOption": "None"
           },
-          "firstRowOnly": false,
           "datasetSettings": {
             "annotations": [],
             "linkedService": {
-              "name": "sql_erp_control",
+              "name": "WH_Control",
""")

    w("on-call-notes.md", """# On-call notes (Tue 2026-10-13)

- 06:40 Pager: PL_Nightly_ERP_Load failed, errorCode ERP_LOAD_FAILED. Finance dashboards show yesterday's
  numbers. NB_Silver_ERP ran at 04:00 and processed 0 new bronze rows.
- 06:45 Monitoring hub: run took 11 seconds. Fail activity message just says "see the activity runs".
- 06:50 Yesterday's run took 1h47m (normally ~40 min) and the copy for SalesOrderLine had a DTU
  recommendation. Is the source DB throttling us again? Ticket open with the ERP DBA team.
- 06:55 Nobody touched the ERP database. PR #412 (control table move) was deployed yesterday afternoon.
- Exported the last two runs to incident/runs/. Control table preview in incident/control-table-preview.csv.
""")

    with open(os.path.join(ROOT, "warehouse", "WH_Control", "etl", "load_control_seed.csv")) as f:
        w("control-table-preview.csv", f.read())

    print(f"incident bundle written to {INC}")
    print(f"current pipeline dry-run status: {failed['status']}")


if __name__ == "__main__":
    main()
