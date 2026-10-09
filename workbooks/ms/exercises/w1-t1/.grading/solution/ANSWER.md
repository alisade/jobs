# ANSWER: ms/w1-t1

## Approach
Started from the failed run 7c0a3f52 in the Monitoring hub (incident/runs/2026-10-13T0200Z_*.json). The pipeline
ran 11 seconds; the Fail activity message is generic, so I opened the activity runs. LookupTables succeeded,
ForEachTable failed before any iteration, so no Copy ran (which is why NB_Silver_ERP found 0 new rows).
Ruled out source throttling: the DTU recommendation is from the 2026-10-12 run that succeeded (slow copy of
SalesOrderLine, 107 min), and in the failed run no Copy activity ever started, so the source was never queried.
Then compared the definition against PR #412 in incident/git-log.txt.

## Root cause
LookupTables runs with firstRowOnly = true. PR #412 re-created the connection in the editor and the
`"firstRowOnly": false` line was dropped from the definition (diff: `-          "firstRowOnly": false,`); the
property defaults to true. With firstRowOnly true the Lookup output is `{"firstRow": {...}}` with no `value`
array, so the ForEach items expression fails:

    ForEachTable  InvalidTemplate: The expression 'activity('LookupTables').output.value' cannot be evaluated
    because property 'value' doesn't exist, available properties are 'firstRow, effectiveIntegrationRuntime,
    billingReference, durationInQueue'.

Evidence the Lookup itself was fine: its run output holds `firstRow` with load_id 1 (Sales.SalesOrderHeader).

Latent second fault from the same PR: the control-table columns were renamed (schema_name -> source_schema,
table_name -> source_table, see load_control.sql and the Lookup SELECT list), but CopyTable still used
`item().schema_name` / `item().table_name`. After fixing firstRowOnly the dry run fails on every iteration with
"property 'schema_name' doesn't exist, available properties are 'load_id, source_schema, source_table, ...'".

## Fix
- LookupTables: `"firstRowOnly": false`.
- CopyTable source query: `[@{item().source_schema}].[@{item().source_table}]`.
Verified with `make simulate` (pipeline Succeeded, 4 copies, 4 watermark updates, CRM and disabled rows
skipped) and `make test`. Then rerun the pipeline once for the 2026-10-13 window; the watermark only moves
after a successful copy, so the rerun picks up everything since 2026-10-11 02:00.

## Trade-offs / what I would do in production
- Deploy pipeline changes only after a dev/test run in a deployment pipeline stage; a single test run would
  have caught both faults.
- Make the Fail activity message carry the real error, e.g.
  `@activity('ForEachTable').error.message`, so the pager shows the cause.
- Add a data-freshness alert (Activator or a check on max ModifiedDate in bronze) so "succeeded with zero rows"
  is caught too.
- Bound the incremental window (`> last_watermark AND <= trigger time`) so rows modified during the copy are not
  skipped. The SalesOrderLine slowness is a separate capacity issue for the ERP DBA team.
