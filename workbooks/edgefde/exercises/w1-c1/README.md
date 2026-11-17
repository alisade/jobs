# edgefde/w1-c1 - Idempotent vibration-feature ingest with a safe backfill

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 1 (Tue: Kafka as a client author; Wed: delivery semantics and idempotency; Thu: backfills and data quality)

## Scenario

You are the forward deployed engineer at Tessellate Edge, embedded with Corvane Industrial's
reliability team at their Dunmore pump plant (both fictional). Edge gateways on four pumps compute
one feature record per 60-second window (RMS, peak, kurtosis, four band energies) and publish it over
MQTT; a bridge forwards it to the Kafka topic `vibration.features`, keyed by device id.

The plant's first prototype consumer wrote rows with a plain `INSERT` and autocommit. After the
first broker failover the dashboards showed duplicated windows, and a half-finished backfill of
2026-10-14 left that day with 1.3x the expected rows. The reliability lead wants a consumer and a
backfill command that can be killed and rerun at any point without changing the numbers, and that
refuse to load a day that is obviously incomplete.

Locally, Kafka is an in-process fake (`ingest/broker.py`, complete, read its docstring) with real
consumer-group semantics: committed offsets survive a crash, positions do not.

## What you have

| Path | What it is |
|---|---|
| `ingest/broker.py` | Fake Kafka: topics, partitions keyed by crc32(key), consumer groups, `poll` / `commit` (do not edit) |
| `ingest/models.py` | The message contract (TODO) |
| `ingest/store.py` | SQLite feature store, the prototype's non-idempotent draft (TODO) |
| `ingest/consumer.py` | The consumer loop (TODO) |
| `ingest/dq.py` | Data quality checks for a day (TODO) |
| `ingest/backfill.py` | Backfill function and CLI (TODO) |
| `scripts/gen.py` | Deterministic data: `make setup` writes `archive/2026-10-14` (good, with 5 invalid lines and some duplicate lines) and `archive/2026-10-15` (pump-03 lost about 20% of its windows) |
| `scripts/demo.py` | `make demo`: one hour of traffic through the fake broker into your consumer |

## Your task

### Message contract (`models.py`)

`parse_record(raw: bytes) -> FeatureRecord`, raising `InvalidRecord("<short reason>")` for anything
that breaks these rules:

- valid JSON object; unknown extra fields are ignored (a newer gateway firmware must not stop the line)
- `schema_version` 1 or 2 (default 1); v2 adds optional `temperature_c`
- `device_id` matches `^[a-z0-9][a-z0-9-]{1,31}$`
- `window_start` is an ISO-8601 timestamp **with** an offset (naive timestamps are rejected); it is
  normalised to UTC
- `window_s` 1..3600, `seq` >= 0, `rms` >= 0, `peak` >= 0, `kurtosis` any finite number
- `band_energy` exactly 4 finite values, each >= 0; no NaN or infinity anywhere
- `FeatureRecord.key` is `(device_id, "YYYY-MM-DDTHH:MM:SSZ")` in UTC: the idempotency key

### Store (`store.py`)

- `write_batch(records, quarantined)` writes the valid records and the quarantine rows
  `(raw, reason, source)` in **one** transaction: either all of it lands or none of it.
- Upsert keyed by `(device_id, window_start)`; when the key exists, keep the row with the **higher
  `seq`** (a late replay of an older reading must not overwrite a newer one).
- Quarantine rows are unique by `source`, so a redelivered bad message is stored once.

### Consumer (`consumer.py`)

- `run_once(consumer, store, max_records)`: poll, parse every message, write valid and invalid ones in
  one `write_batch` (source `"<topic>/<partition>/<offset>"`), and **then** `consumer.commit()`. If the
  write raises, do not commit; let the exception propagate (the supervisor restarts the process).
- `run_until_idle(...)` loops until a poll returns nothing and returns the summed `BatchResult`.

### Data quality (`dq.py`)

`check_day(records, day, expected_devices, window_s=60, min_completeness=0.95, max_outlier_rate=0.01)`
returns a list of `Issue(check, detail)`, empty when the day is fine. Checks, using these exact
`check` names:

| check | fails when |
|---|---|
| `in_partition` | any record's `window_start` is not on `day` (UTC) |
| `device_present` | an expected device has no records |
| `completeness` | an expected device has fewer than `min_completeness` of the `86400 / window_s` distinct windows (put the device id in `detail`) |
| `unknown_device` | a device that is not expected appears |
| `rms_range` | more than `max_outlier_rate` of the day's records have `rms > 50` g |

Duplicates must not inflate completeness.

### Backfill (`backfill.py`)

- `backfill(store, archive_dir, day, expected_devices)` reads every `*.jsonl` under
  `archive_dir/<day>/`, parses each line (invalid lines are quarantined with source `"<file>:<line>"`),
  runs `check_day` on the valid records and raises `DataQualityError(issues)` **before writing
  anything** if there is any issue. Otherwise it writes in one transaction and returns
  `BackfillResult(day, read, valid, quarantined, written, rows_for_day)`.
- `python -m ingest.backfill --db ... --archive ... --day YYYY-MM-DD --devices a,b,c`: exit 0 and a
  one-line summary on success; exit 2 with the issues on stderr when data quality fails.

## Acceptance criteria (what the grader checks)

- Every contract rule above, including NaN/infinity, naive timestamps and unknown fields.
- Killing the consumer between poll and write, or a failing write, never loses or duplicates a window;
  offsets never move past data that is not in the store.
- A batch is atomic: a failure mid-batch leaves neither features nor quarantine rows.
- Higher `seq` wins; redelivered bad messages are quarantined once.
- Backfilling 2026-10-14 any number of times, before or after live ingest of the same day, gives
  exactly 5760 rows; 2026-10-15 fails with a `completeness` issue for pump-03 and writes nothing.
- `ANSWER.md` explains your delivery semantics in one paragraph (what "effectively once" means here
  and what it relies on) and how you would run this in production.

## How to run

```bash
make setup                     # shared venv + archive/
make demo                      # your consumer over an hour of fake traffic
make backfill DAY=2026-10-14   # the CLI
make test                      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade edgefde/w1-c1
make clean
```

## What to submit

Your changes under `ingest/` and a filled-in `ANSWER.md`. Do not edit `ingest/broker.py` or `scripts/`.
