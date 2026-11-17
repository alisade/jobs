# ms/w2-c1: Eventhouse KQL pack for fleet telemetry

Type: coding. Estimate: 2 h. Exam: DP-700 - Ingest and transform data (30-35%), streaming half; Monitor and optimize (30-35%).

## Scenario

Contoso Fleet streams telematics from 1,400 trucks and vans. An Eventstream lands every JSON event
into `RawTelemetry` (one `dynamic` column) in the FleetOps Eventhouse. The platform team created the
tables (see `schema.kql`) and left the rest to you before Monday's go-live:

- the ops dashboard tile needs 5-minute speed/temperature windows,
- dispatch wants a "where is every vehicle now" query,
- `Telemetry` must be filled by an **update policy**, not by a notebook,
- Eventstream delivers at-least-once, so retried events (same `EventId`) must be deduplicated,
- finance wants trips (engine-on periods) to bill per-trip usage.

Everything you write is reviewed by the data platform lead and deployed by a script that runs your
`.kql` files as-is. There is no Kusto engine on this machine, so the grader parses your KQL
structurally (operators, clause contents, arguments, command shapes and policy JSON) and the rubric
covers the rest. If you have the Fabric trial, paste each query into a KQL queryset and run it against
`data/telemetry_sample.csv` ingested into a scratch table; it is the best way to check the results below.

## Your task

Fill in the five files in `queries/` (each has TODOs):

1. `01_speed_5min.kql` - last hour, per vehicle, 5-minute tumbling windows. Output columns, which the
   tile binds to by name: `VehicleId, Window, AvgSpeedKph, MaxEngineTempC, Readings`.
2. `02_latest_per_vehicle.kql` - one row per vehicle seen in the last day with its latest reading.
   Output: `VehicleId, LastSeen, SpeedKph, FuelPct, Lat, Lon`.
3. `03_update_policy.kql` - a stored function `ParseRawTelemetry()` that turns `RawTelemetry.Payload`
   (shape: `data/raw_sample.json`) into exactly the `Telemetry` schema and drops rows without a
   timestamp or vehicle id; then the `.alter table Telemetry policy update` command. The policy must be
   safe for production.
4. `04_materialized_view.kql` - materialized view `TelemetryDedup` over `Telemetry`, one row per
   `EventId`, backfilled from existing rows, with a lookback that bounds the dedupe work
   (retries arrive within minutes).
5. `05_trips.kql` - trips per vehicle: consecutive (deduplicated) readings less than 10 minutes apart
   form one trip; cap a trip at 12 hours. Output: `VehicleId, TripStart, TripEnd, Readings, MaxSpeedKph`.

Then fill in `ANSWER.md`.

## Acceptance criteria

- Window query: time filter before `summarize`; `by` list is exactly the vehicle and `bin(Timestamp, 5m)`
  aliased `Window`; aggregates named as above; no `take`/`limit`/`sample`.
- Latest query: `arg_max(Timestamp, *) by VehicleId`, bounded by a time filter, no sort/top shortcuts,
  documented output columns.
- Update policy: function reads `RawTelemetry` by plain name; final `project` matches `Telemetry` column
  names, order and types (correct `to*()` casts); every payload path exists in the sample; bad rows
  filtered. Policy JSON is a one-element array with valid property names, enabled, `Source`
  `RawTelemetry`, `Query` calling the function, and transactional.
- Materialized view: correct `.create ... materialized-view ... on table` shape; `backfill=true` used
  with `async`; `lookback` set (hours); `summarize` is the last and only aggregation step; no
  `now()`/`ago()`, `sort`, `top`, `take`, `partition` or `serialize` in the view query; dedupe key `EventId`
  with `take_any(*)` or `arg_max(Timestamp, *)`.
- Trips: reads deduplicated data; uses `row_window_session()` (with a vehicle restart condition),
  `prev()` + `row_cumsum()`, or `scan`; input explicitly ordered by vehicle then `Timestamp asc`;
  10-minute gap and 12-hour cap; documented output columns.
- No `TODO` left in `queries/`.

## Sample data and expected results

`data/telemetry_sample.csv` has 42 rows (41 distinct `EventId`s: `e-0035`, a VAN-201 reading, was
re-sent by an Eventstream retry). Run "now" as 2026-10-20 09:40Z.

01, windows for TRK-102 and VAN-201 (TRK-101 omitted for space). Note the VAN-201 09:05 window counts
the duplicate: windows read `Telemetry`, not the view, and that is acceptable for a live tile.

| VehicleId | Window | AvgSpeedKph | MaxEngineTempC | Readings |
|---|---|---|---|---|
| TRK-102 | 09:00 | 41.0 | 84.5 | 2 |
| TRK-102 | 09:05 | 46.0 | 86.0 | 3 |
| TRK-102 | 09:10 | 51.0 | 87.0 | 2 |
| TRK-102 | 09:30 | 32.0 | 82.4 | 2 |
| TRK-102 | 09:35 | 42.0 | 83.6 | 3 |
| VAN-201 | 09:00 | 25.5 | 79.2 | 2 |
| VAN-201 | 09:05 | 27.0 | 79.4 | 2 |
| VAN-201 | 09:10 | 28.0 | 79.6 | 1 |

02, latest per vehicle:

| VehicleId | LastSeen | SpeedKph | FuelPct |
|---|---|---|---|
| TRK-101 | 09:38:05 | 67 | 72.4 |
| TRK-102 | 09:39:20 | 46 | 50.8 |
| VAN-201 | 09:32:50 | 33 | 64.4 |

05, trips (from deduplicated data):

| VehicleId | TripStart | TripEnd | Readings | MaxSpeedKph |
|---|---|---|---|---|
| TRK-101 | 09:00:05 | 09:38:05 | 20 | 67 |
| TRK-102 | 09:01:20 | 09:13:20 | 7 | 52 |
| TRK-102 | 09:31:20 | 09:39:20 | 5 | 46 |
| VAN-201 | 09:00:50 | 09:32:50 | 9 | 33 |

## How to run

```
make setup     # uv venv with pytest
make test      # visible smoke checks (the grader is much stricter)
make clean
```

Grade from the workbooks root: `/grade ms/w2-c1`.

## What to submit

The five files in `queries/` and `ANSWER.md`. Do not edit `schema.kql` or `data/`.

## Study guide links

- [Week 2 Tue - Eventhouse and KQL](../../../../microsoft-adf-powerapps-study-plan.html#week2)
- [Update policy overview](https://learn.microsoft.com/en-us/kusto/management/update-policy?view=microsoft-fabric)
- [Create materialized view](https://learn.microsoft.com/en-us/kusto/management/materialized-views/materialized-view-create?view=microsoft-fabric)
- [bin()](https://learn.microsoft.com/en-us/kusto/query/bin-function?view=microsoft-fabric) /
  [arg_max()](https://learn.microsoft.com/en-us/kusto/query/arg-max-aggregation-function?view=microsoft-fabric) /
  [row_window_session()](https://learn.microsoft.com/en-us/kusto/query/row-window-session-function?view=microsoft-fabric) /
  [scan](https://learn.microsoft.com/en-us/kusto/query/scan-operator?view=microsoft-fabric)
