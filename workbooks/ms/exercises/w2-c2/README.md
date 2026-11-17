# ms/w2-c2: Nightly orchestration pipeline with polling, fan-out and failure paths

Type: coding. Estimate: 2 h. Exam: DP-700 - Implement and manage an analytics solution (30-35%): orchestration; Monitor and optimize (30-35%): identify and resolve pipeline errors.

## Scenario

Northwind Logistics runs its nightly order load in Microsoft Fabric. Today it is three pipelines that an
operator starts by hand in the right order and watches. The data platform lead wants one parent
pipeline, `pl_nightly_orchestrator`, committed to the workspace git repo (Fabric git format:
`pl_nightly_orchestrator.DataPipeline/pipeline-content.json`). The on-call runbook and the alert rules
already refer to the activity names and error codes below, so they are fixed.

The flow:

1. A notebook stages yesterday's orders into the lakehouse.
2. A partner (the 3PL carrier) must then build an export. Their REST API starts an export
   asynchronously and returns `{"exportId": "..."}`; you poll `GET /v1/exports/{exportId}` until
   `status` is `Completed` or `Failed`. Exports usually take 5-20 minutes and have hung for hours twice.
3. When the export completed, a child pipeline loads each region in parallel, three at a time.
4. Every failure must end the run in a **Fail** activity with a specific error code, so the run shows
   Failed in the Monitoring hub and the alert routes on `errorCode`.

## Your task

Edit `pl_nightly_orchestrator.DataPipeline/pipeline-content.json` (the starter has TODO descriptions and
deliberate gaps) to meet this spec, then fill in `ANSWER.md`.

Parameters and variables:

| Name | Kind | Type | Default |
|---|---|---|---|
| `load_date` | parameter | String | `""` (the notebook treats empty as yesterday) |
| `env` | parameter | String | `"dev"` |
| `regions` | parameter | Array | `["east", "west", "central"]` |
| `export_status` | variable | String | `"Pending"` |

Activities (top level unless noted):

| Name | Type | Runs when | Requirements |
|---|---|---|---|
| `nb_stage_orders` | Notebook (`TridentNotebook`) | start | notebookId `6c1f0e2a-4b7d-4c55-9a0e-2f8d3b1e7a10`, workspaceId `0b5e9d2c-71aa-4f3e-8c6b-5d2a9e4f1c33`; base parameters `load_date` and `env` (type `string`) from the pipeline parameters; policy timeout 2 h, retry 2, retry interval 120 s |
| `web_start_export` | Web (`WebActivity`) | notebook Succeeded | `POST /v1/exports`; JSON body with `loadDate` (from `load_date`) and `runId` (`pipeline().RunId`); retry 3, interval 30 s, timeout at most 10 minutes |
| `until_export_done` | Until | export started Succeeded | stops when `export_status` is `Completed` **or** `Failed`; timeout 1 h |
| `web_get_export_status` | Web, inside the Until | first | `GET` `/v1/exports/<exportId from web_start_export output>` as an expression |
| `set_export_status` | Set variable, inside the Until | after the GET Succeeded | `export_status` = the GET output `status` |
| `wait_poll` | Wait, inside the Until | after the Set Succeeded | 30-300 s poll interval |
| `fail_export_timeout` | Fail | Until Failed | errorCode `EXPORT_TIMEOUT` |
| `if_export_failed` | If condition | Until Succeeded | expression `export_status == 'Failed'`; true branch: `fail_export` (Fail, errorCode `EXPORT_FAILED`) |
| `foreach_region` | ForEach | If condition Succeeded | items `regions`; parallel, batch count 3 |
| `invoke_region_load` | Invoke pipeline, inside the ForEach | - | child pipelineId `a3d7c9e1-2f4b-4e8a-b1c6-7e9f0d2a5b48` in the same workspace; wait on completion; parameters `region` = current item, `load_date`, `env` |
| `fail_staging` | Fail | notebook Failed | errorCode `STAGING_FAILED` |
| `fail_region_loads` | Fail | ForEach Failed | errorCode `REGION_LOAD_FAILED` |

Every Fail message must include `pipeline().RunId` so on-call can jump to the run.

## Acceptance criteria

- `make lint` reports 0 errors: known activity types, unique names, `dependsOn` targets in the same scope,
  valid dependency conditions, no cycles, `D.HH:MM:SS` timeouts, retry interval 30-86400 s, no retry on
  control activities, declared parameters/variables, `activity('X')` only for upstream activities,
  `item()` only inside a ForEach, no Set variable inside a parallel ForEach.
- Every row of the tables above is implemented exactly (names, types, conditions, policies, error codes).
- Happy-path activities depend only on `Succeeded`; each failure path depends only on `Failed` of the
  activity it handles.
- No `TODO` left in the JSON. `ANSWER.md` explains your design choices.

## Format notes and simplifications

- The JSON follows the Fabric git format for a Data pipeline item (`properties.activities`,
  `properties.parameters`, `properties.variables`, a `.platform` file). Activity JSON mirrors Azure Data
  Factory: `dependsOn[].dependencyConditions`, `policy.timeout` as `D.HH:MM:SS`, expressions as
  `{"value": "@...", "type": "Expression"}`.
- Fabric Web and Invoke pipeline activities reference a **connection** (`externalReferences.connection`);
  Web uses `relativeUrl` against the connection's base URL. The linter accepts `url` too.
- Fabric has two Invoke pipeline activities: the new one (`InvokePipeline`, `operationType`
  `InvokeFabricPipeline`, `pipelineId`, `workspaceId`, connection) and the legacy one (`ExecutePipeline`,
  same workspace only). The grader accepts either; prefer the new one.
- Nothing here runs: there is no Fabric engine locally. The grader validates structure and references
  the way the designer and the run-time expression evaluator would.

## How to run

```
make setup   # uv venv with pytest
make lint    # generic structural linter (also in make test)
make test    # visible tests
make clean
```

Grade from the workbooks root: `/grade ms/w2-c2`.

## What to submit

`pl_nightly_orchestrator.DataPipeline/pipeline-content.json` and `ANSWER.md`. Do not edit `lint/` or `tests/`.

## Study guide links

- [Week 1 Wed - Data Factory pipelines](../../../../microsoft-adf-powerapps-study-plan.html#week1)
- [Week 2 Fri - Orchestration patterns](../../../../microsoft-adf-powerapps-study-plan.html#week2)
- [Notebook activity](https://learn.microsoft.com/en-us/fabric/data-factory/notebook-activity)
- [Invoke pipeline activity](https://learn.microsoft.com/en-us/fabric/data-factory/invoke-pipeline-activity)
- [Until activity](https://learn.microsoft.com/en-us/fabric/data-factory/until-activity) /
  [ForEach activity](https://learn.microsoft.com/en-us/fabric/data-factory/foreach-activity) /
  [Fail activity](https://learn.microsoft.com/en-us/fabric/data-factory/fail-activity)
- [Expressions and functions](https://learn.microsoft.com/en-us/fabric/data-factory/expression-language)
