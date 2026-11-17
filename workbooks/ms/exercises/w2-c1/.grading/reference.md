# Reference: ms/w2-c1

Reference files are in `.grading/solution/queries/`.

## Key points

- **bin() windows.** `bin(Timestamp, 5m)` floors to 5-minute boundaries; those are tumbling windows. A
  hopping window needs `range` + `mv-expand` or a materialized view per offset. Put the time filter
  before `summarize` so the engine prunes extents by time.
- **arg_max(Timestamp, \*) by Key** returns the latest whole row per key. `top 1 by Timestamp` or
  `sort | take` give one row overall. `arg_max(Timestamp, *)` is also the canonical "latest record"
  materialized-view shape.
- **Update policy.** Defined on the *target* table; `Source` names the source table; `Query` calls a
  stored function. The function output must match the target table's column names, order and types.
  `IsTransactional: true` makes a failing policy fail the source ingestion, which is then retried: no
  silent loss. With `false` the source keeps the data and the target misses it, and only
  `.show ingestion failures | where OriginatesFromUpdatePolicy == true` tells you.
- **Materialized views.** A single `summarize` as the last operator; supported aggregations include
  `take_any`, `arg_max`, `count`, `dcount`, `sum`, `avg`. No `now()`-dependent filters (use retention),
  no `sort`/`top`/`partition`/`serialize`. `backfill=true` requires `.create async`. `lookback` limits
  the part of the view merged with each delta: faster, but a duplicate older than the lookback survives.
- **Sessions.** `row_window_session(Expr, MaxDistanceFromFirst, MaxDistanceBetweenNeighbors, Restart)`
  needs serialized input. `sort by` defaults to **descending**, so write `Timestamp asc` explicitly.
  Alternatives: `prev()` + `row_cumsum()`, or `scan` with a declared state column.

## Interview angles

- When would you use Eventstream processing instead of an update policy? (Simple filter/projection
  before landing, routing to several destinations; update policies win for KQL-native parsing and
  multiple derived tables.)
- What happens to the materialized view if someone adds a column to `Telemetry`? (`take_any(*)`/`arg_max(*)`
  views can break or need `autoUpdateSchema`; the view gets disabled on schema mismatch.)
- How do you dedupe without a materialized view, and what does it cost at query time?
