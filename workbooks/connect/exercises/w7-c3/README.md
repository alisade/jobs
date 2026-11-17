# connect/w7-c3 - Contact record pipeline: Firehose transform and Athena-style KPI SQL

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 7 (data streaming: Kinesis, Amazon Data Firehose, Glue/Athena); Week 2 (KPIs: service level, abandon rate, AHT, occupancy, containment)

## Scenario

LFG streams Amazon Connect contact records (CTRs) to a Kinesis data stream. An Amazon Data Firehose
delivery stream (formerly Kinesis Data Firehose) reads it, calls a transformation Lambda, and writes
newline-delimited JSON to `s3://lfg-connect-lake/ctr/` with dynamic partitioning; Glue catalogs it
and Athena powers the help desk dashboards. The pilot version of the Lambda had three findings from
the data-protection review and one outage:

- raw caller phone numbers and a bot-captured card number landed in the lake (PCI and privacy scope);
- one malformed record failed the whole batch and Firehose retried it for an hour (outage);
- synthetic canary calls (`synthetic=true`) inflated volume by 6%;
- retention could not be applied per contact because nothing told S3 lifecycle which class a contact
  belongs to. LFG policy: legal hold > recorded voice 7 years > everything else 3 years.

The BI team also wants three views that run unchanged on Athena: daily queue KPIs, agent occupancy
and self-service containment.

## What you have

| Path | What it is |
|---|---|
| `pipeline/transform.py` | the Firehose transformation Lambda (`lambda_handler`) |
| `sql/kpis.sql` | KPI views over table `contacts` (transformed rows) and `agent_staffing` |
| `data/sample-ctrs.jsonl` | 180 contact records (Connect contact record data model subset), 3 days |
| `data/agent_staffing.csv` | staffed seconds per agent per day (from agent event stream rollups) |
| `scripts/run_local.py` | `make run`: sample -> Lambda -> `out/channel=.../dt=.../retention=.../` -> DuckDB views |
| `tests/helpers.py` | builds Firehose events, decodes results, loads DuckDB (`contacts`, `agent_staffing`) |

## Requirements

Firehose contract (per input record): echo `recordId`; `result` is `Ok`, `Dropped` or
`ProcessingFailed`; `data` is base64; on `Ok` also `metadata.partitionKeys`.

1. Undecodable or non-CTR records (no `ContactId`/`InitiationTimestamp`): `ProcessingFailed` with the
   original `data`; the rest of the batch still succeeds. Synthetic canaries: `Dropped`.
2. Output one JSON object per contact followed by `\n`, with these columns: `contact_id,
   initial_contact_id, channel, initiation_method, initiation_ts, disconnect_ts, dt (UTC date of
   initiation), duration_seconds, queue_name, queue_seconds, agent_username, answered (agent connected),
   abandoned (queued, never answered), contained (no queue, no agent, selfServiceOutcome=resolved),
   talk_seconds, hold_seconds, acw_seconds, handle_seconds (talk+hold+acw; null if unanswered),
   disconnect_reason, lex_intent, caller_verified (bool), phone_hash, phone_last4, recorded,
   retention_class, attributes`.
3. PII: never output the raw phone number: `phone_hash = sha256(PHONE_HASH_SALT + number)` (env var) and
   `phone_last4`. Remove attributes named ssn, dob, cardNumber, cvv, pin, password (case-insensitive).
   In remaining attribute values replace SSNs (`ddd-dd-dddd`) and Luhn-valid 13-19 digit card numbers
   (spaces/dashes allowed) with `[REDACTED]`; leave non-Luhn digit runs (order numbers) alone.
4. `retention_class`: `legal-hold` | `recorded-7y` | `standard-3y`. Partition keys: `channel` (lower
   case), `dt`, `retention`.
5. SQL (`sql/kpis.sql`), portable to Athena (Trino): standard `CASE`, `CAST(... AS DOUBLE)`, `NULLIF`, no
   DuckDB-only functions.
   - `queue_daily(dt, queue_name, offered, answered, abandoned, short_abandons, abandon_rate,
     service_level_60s, avg_handle_seconds)`: service level = answered within 60 s / (offered - abandons
     under 5 s); rates rounded to 4 places, AHT to 1.
   - `agent_occupancy(dt, agent_username, contacts, handle_seconds, staffed_seconds, occupancy)`: one row
     per staffing row, including agents with no contacts.
   - `containment_by_intent(lex_intent, contacts, contained, containment_rate)`: null intent as `none`.

## Acceptance criteria (what the grader checks)

- Firehose contract, Dropped/ProcessingFailed semantics, batch survives bad records.
- Columns, flags, durations, handle time; partition keys; retention classes.
- No raw phone number anywhere in the output; salted hash; deny-listed attributes gone; SSN and
  Luhn-valid cards redacted in free text, non-Luhn numbers kept.
- The three views return the expected numbers on the sample (computed independently from the CTRs).
- `ANSWER.md`: the S3 lifecycle and Glue/Athena setup you would put around this, and what you would
  alarm on.

## How to run

```bash
make setup     # shared Python venv (connect/.venv: pytest, duckdb)
make test      # visible tests
make run       # end to end on the sample (the starter crashes on the malformed record: that is the outage)
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade connect/w7-c3
make clean
```

Real-world notes: Firehose dynamic partitioning can take keys from the Lambda's
`metadata.partitionKeys` and use them in the S3 prefix (`ctr/channel=!{partitionKeyFromLambda:channel}/...`).
`ProcessingFailed` records go to the error output prefix. S3 lifecycle rules can then expire objects
per `retention=` prefix; legal hold is better enforced with S3 Object Lock than with a prefix.
