# ms/w2-c1 ANSWER

## Approach
- 01: filter `Timestamp > ago(1h)` first so only recent extents are scanned, then `summarize ... by VehicleId, Window = bin(Timestamp, 5m)`. `bin()` gives tumbling windows aligned to the epoch.
- 02: `arg_max(Timestamp, *) by VehicleId` returns the full latest row per vehicle in one pass; a `sort | take` returns N rows overall, not one per vehicle.
- 03: `ParseRawTelemetry()` projects the exact `Telemetry` columns in order with `todatetime/tostring/toreal`, and drops rows without a timestamp or vehicle. The policy is transactional so a failed transform fails the source ingestion (and it is retried) instead of silently skipping rows.
- 04: `take_any(*) by EventId` is the cheapest dedupe view; `backfill=true` needs `.create async`; `lookback=6h` limits the merge to recent records because retries arrive within minutes.
- 05: reads `TelemetryDedup`, sorts by vehicle then `Timestamp asc`, and `row_window_session(Timestamp, 12h, 10m, VehicleId != prev(VehicleId))` starts a new session per vehicle or after a 10-minute gap.

## Fix
None needed in the schema. I would set a short soft-delete retention on `RawTelemetry` once the policy is proven.

## Trade-offs / what I would do in production
- Update policy keeps the transform inside the Eventhouse with no orchestration; Eventstream processing is fine for simple filters but cannot dedupe historically.
- Querying `TelemetryDedup` costs less than a query-time `summarize by EventId`, but the lookback trades completeness for speed: a retry older than 6h would survive as a duplicate.
- Test with `.set-or-append` into scratch tables in a dev KQL database, then compare outputs with the expected tables before promoting through the deployment pipeline.
