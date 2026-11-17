# ms/w2-t1 ANSWER

## Approach
1. Followed the data: `eventstream_metrics.csv` shows ~30 events/min in and out to both destinations with 0 conversion/runtime errors, so the source and Eventstream are fine.
2. `kql_01_landing_vs_enriched.txt`: `TelemetryLanding` keeps ~150 rows per 5 min after 09:40, `TelemetryEnriched` drops to 3 then 0. So ingestion works and the loss is between landing and enriched.
3. `kql_02_landing_null_profile.txt`: from the 09:40 bin on, every landed row has empty `DeviceId`, null `Timestamp` and null `SpeedKph`. `kql_03_landing_sample_rows.txt` shows rows with only `VehicleId` populated.
4. The update policy (`kql_06_update_policy.txt`, `EnrichTelemetry.kql`) filters `isnotempty(DeviceId) and isnotnull(Timestamp)`, so it correctly drops every such row; no failure is raised, which is why `kql_04_show_ingestion_failures.txt` is empty.
5. Ruled out capacity: `capacity_metrics.txt` shows interactive delay 09:15-09:20 from `nb_backfill_trips`, back to 64% by 09:30, i.e. before the break and unrelated to ingestion.

## Root cause
The gateway release 4.2.0 (`telemetry-gateway_git_log.txt`, commit 7c2e9a4, rolled out 09:38) changed the event envelope: `deviceId` became `device.id`, `fw` became `device.fw`, the ISO `ts` string became `tsMs` (epoch milliseconds), and the sensor values moved under `telemetry` (`telemetry.speedKph`, `telemetry.engineTempC`, `telemetry.fuelPct`). `eventstream_data_preview.jsonl` shows both shapes either side of 09:40. The deployed `TelemetryLanding_mapping` (`kql_05_show_mappings.txt`, last updated 2026-08-14) still uses `$.ts`, `$.deviceId`, `$.speedKph` and so on. A JSON path that does not exist yields null rather than an ingestion error, so rows landed with nulls everywhere except `VehicleId`, and the update policy's quality filter removed all of them from `TelemetryEnriched`.

## Fix
- Updated `eventhouse/mappings/TelemetryLanding_mapping.json`: `Timestamp` from `$.tsMs` with `Transform: DateTimeFromUnixMilliseconds`, `DeviceId` from `$.device.id`, `FirmwareVersion` from `$.device.fw`, sensor values from `$.telemetry.*`. Applied with `.alter table TelemetryLanding ingestion json mapping "TelemetryLanding_mapping" '<json>'`; the Eventstream destination references the mapping by name, so no Eventstream change is needed.
- Verified with `make replay`: post-09:40 preview events now land with all columns populated and millisecond timestamps; then in prod `TelemetryEnriched | where ingestion_time() > ago(5m) | count` goes non-zero and the Activator rule shows new events.
- Update policy left unchanged: it is transactional and its filter is correct.
- Backfill: the 09:40-fix rows in `TelemetryLanding` are unrecoverable from the table (fields are null). Re-ingest that window from the raw copy in `lh_fleet_raw` (or Eventstream retention) into `TelemetryLanding` with the fixed mapping, which triggers the update policy; then delete the null rows from landing (`.delete table TelemetryLanding records <| TelemetryLanding | where isnull(Timestamp) and ingestion_time() between (...)`).

## Trade-offs / what I would do in production
- Contract: producers publish a schema version (`schemaVersion` exists now) and changes go through a review with consumers; CI on the gateway replays sample events through the production mapping.
- Monitoring: alert on the null ratio of key columns in `TelemetryLanding` and on `TelemetryEnriched` freshness, because a mapping miss never shows in `.show ingestion failures`.
- Resilience: also land the whole event as `dynamic` (`Path: "$"` into a `RawPayload` column) and parse in the update policy with `coalesce(Payload.tsMs, ...)`, so a shape change is fixable by redeploying a function and replaying, not by losing fields. The trade-off is storage and more parsing work in the update policy.
