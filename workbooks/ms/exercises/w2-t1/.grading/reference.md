# Reference: ms/w2-t1

Fixed mapping: `.grading/solution/eventhouse/mappings/TelemetryLanding_mapping.json`. Model answer:
`.grading/solution/ANSWER.md`.

## Root cause in one line

Gateway 4.2.0 moved and renamed fields (`deviceId` -> `device.id`, `ts` ISO -> `tsMs` epoch ms,
`speedKph` -> `telemetry.speedKph`, ...). The JSON ingestion mapping still pointed at the old paths.
Missing paths become nulls, not ingestion failures, so `TelemetryLanding` kept filling with empty rows
and the transactional update policy's quality filter dropped all of them from `TelemetryEnriched`.

## Why the obvious checks were green

- Eventstream metrics count messages, not column completeness.
- `.show ingestion failures` only lists failed ingestions (and failed update policies). A filter that
  returns zero rows is a success.
- Capacity throttling at 09:15-09:25 was a notebook backfill, finished before the break: the red herring.

## Fix details

- `Timestamp`: `{"Path": "$.tsMs", "Transform": "DateTimeFromUnixMilliseconds"}`. Seconds would be off
  by 1000x; ISO parsing of a number yields null.
- Apply with `.alter table TelemetryLanding ingestion json mapping "TelemetryLanding_mapping" '...'`.
- Backfill from `lh_fleet_raw` (or Eventstream retention), then delete the null rows.

## Interview angles

- Why might you prefer landing the raw event as `dynamic` and parsing in an update policy? What does
  it cost?
- With `IsTransactional: false`, what would have been different during this incident? (Nothing: the
  policy never failed. Transactional matters for query errors and schema mismatches.)
- How would you detect this in under 5 minutes next time? (Freshness and null-ratio alerts via an
  Activator rule on a KQL query.)
