# Reference: ms/w1-t1

## Root cause

PR #412 re-pointed LookupTables at the Fabric Warehouse and re-created the connection in the editor. The
`"firstRowOnly": false` property disappeared from the definition (see the diff in incident/git-log.txt).
`firstRowOnly` defaults to `true`, and then the Lookup output is

```json
{"firstRow": {"load_id": 1, "source_schema": "Sales", ...}, "effectiveIntegrationRuntime": "...", ...}
```

instead of `{"count": 4, "value": [...]}`. The ForEach `items` expression
`@activity('LookupTables').output.value` therefore fails with InvalidTemplate: "property 'value' doesn't exist,
available properties are 'firstRow, effectiveIntegrationRuntime, billingReference, durationInQueue'". No
iteration starts, no Copy runs, the Fail activity turns it into the generic ERP_LOAD_FAILED.

Latent: the same PR renamed control-table columns. CopyTable still referenced `item().schema_name` and
`item().table_name`. That surfaces only after the first fix, on every iteration.

## Fix

```diff
           "partitionOption": "None"
         },
+        "firstRowOnly": false,
         "datasetSettings": {
...
-  "value": "SELECT * FROM [@{item().schema_name}].[@{item().table_name}] WHERE ..."
+  "value": "SELECT * FROM [@{item().source_schema}].[@{item().source_table}] WHERE ..."
```

The solution file is `.grading/solution/pipelines/PL_Nightly_ERP_Load.DataPipeline/pipeline-content.json`.

## Red herring

The DTU recommendation and the 107-minute SalesOrderLine copy are from the 2026-10-12 run, which succeeded,
before PR #412 was deployed. In the failed run nothing reached the source.

## Exam angles

- Lookup limits: 5,000 rows and 4 MB of output; above that, page with an outer/inner pipeline.
- Use `output.firstRow.<col>` for a single row, `output.value` for ForEach.
- Fail activity: custom message and error code; set it from `activity('X').error.message` to keep the cause.
- Dependency conditions: Succeeded, Failed, Skipped, Completed. A Fail activity on the Failed path makes the
  pipeline fail while still running cleanup.

## Interview angles

- How would you test pipeline definitions before they reach prod in Fabric (deployment pipelines, a test
  workspace, parameterized connections via deployment rules or variable libraries)?
- Why does the watermark update only on Succeeded, and what happens on a rerun?
