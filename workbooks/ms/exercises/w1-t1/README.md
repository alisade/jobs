# ms/w1-t1: Nightly ERP load failed and the ForEach never ran

Type: troubleshooting. Estimate: 1-2 h. Exam: DP-700 - Monitor and optimize an analytics solution (30-35%): identify and resolve pipeline errors; also Ingest and transform data (30-35%): metadata-driven loads.

## Scenario

Northwind Traders loads its ERP tables into the `lh_bronze` lakehouse every night with a metadata-driven
Fabric Data pipeline, `PL_Nightly_ERP_Load`: a Lookup reads the list of tables from a control table, a
ForEach copies each table incrementally, and a Script activity moves that table's watermark. The pipeline
definition lives in git (Fabric git integration format: `<name>.DataPipeline/pipeline-content.json`), and so
does the control-table schema (a Warehouse database project under `warehouse/`).

Pager, Tuesday 06:40 UTC:

> PL_Nightly_ERP_Load FAILED (errorCode ERP_LOAD_FAILED). Finance dashboards still show Sunday's numbers.
> NB_Silver_ERP ran at 04:00 and processed 0 new bronze rows. The run only took 11 seconds. Yesterday's
> run was very slow and had a DTU warning, maybe the ERP database is throttling us again?

You are on call. Find out why, fix the pipeline definition, and prove the fix before anyone reruns it in prod.

## What you have

After `make setup`:

- `incident/monitoring-hub-runs.json` - the Monitoring hub list of recent runs.
- `incident/runs/*.json` - exported pipeline runs with their activity runs (input, output, error). The
  2026-10-13 run is produced by dry-running the pipeline definition that is checked in now.
- `incident/git-log.txt` - the most recent merge to main.
- `incident/on-call-notes.md`, `incident/control-table-preview.csv`.
- `pipelines/PL_Nightly_ERP_Load.DataPipeline/` - the pipeline as stored in git.
- `warehouse/WH_Control/` - the control table as deployed (treat it as the source of truth; do not change it).
- `tools/simulate_run.py` - a dry-run simulator. It is not Fabric: it walks the activity graph, evaluates the
  pipeline expression language for the subset this pipeline uses, and fakes the Lookup (reads the control
  table seed, honoring the SELECT list, the WHERE filters and the documented `firstRowOnly` output shapes) and
  the Copy/Script activities. `make simulate` runs it against the current definition.

## Your task

1. Investigate from the evidence the way you would in the Monitoring hub: which activity failed, with what
   error, what did its upstream activity output, and what changed.
2. Fix `pipeline-content.json` so the run succeeds for every enabled `erp` table. Keep the design
   (Lookup -> ForEach -> Copy -> Script); do not hard-code the table list and do not change the warehouse schema.
3. Write `ANSWER.md`: approach, root cause with evidence (quote the error JSON and the lines that prove it),
   the fix and how you verified it, and what you would change so this does not reach prod again.

## Acceptance criteria

- `make simulate` reports `Succeeded`; `make test` passes.
- Exactly the four enabled `erp` tables are copied, each to its `target_table`, and each watermark is updated
  once, only after its copy succeeded.
- Every `item()` property used inside the ForEach is returned by the Lookup query; every `activity()` reference
  points to an upstream activity; every `pipeline().parameters` reference is declared.
- Retry and timeout policies stay sane (retry 1-5, timeout at most 12 hours); ForEach stays parallel (batchCount 1-50).
- `ANSWER.md` names the root cause and backs it with evidence, and explains why the red herring is not the cause.

## How to run

```
make setup      # uv sync + generate incident/
make simulate   # dry-run the current pipeline definition
make test       # visible tests
make clean
```

Then from the workbooks root: `/grade ms/w1-t1`.

## What to submit

The fixed `pipelines/PL_Nightly_ERP_Load.DataPipeline/pipeline-content.json` and a filled `ANSWER.md`.

## Study guide links

- [Week 1 Wed - Data Factory pipelines](../../../../microsoft-adf-powerapps-study-plan.html#week1)
- [Week 3 Thu - Identify and resolve errors](../../../../microsoft-adf-powerapps-study-plan.html#week3)
- [Lookup activity in Fabric](https://learn.microsoft.com/en-us/fabric/data-factory/lookup-activity)
- [Lookup activity output (firstRowOnly)](https://learn.microsoft.com/en-us/azure/data-factory/control-flow-lookup-activity)
- [ForEach activity in Fabric](https://learn.microsoft.com/en-us/fabric/data-factory/foreach-activity)
- [Expressions and functions](https://learn.microsoft.com/en-us/fabric/data-factory/expression-language)
- [Monitoring hub](https://learn.microsoft.com/en-us/fabric/admin/monitoring-hub)
