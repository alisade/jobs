# awsfde/x-1 - Idempotent document-ingestion Lambda

**Type:** coding (optional add-on) | **Estimate:** 2 hours | **Study plan:** Week 7 add-on (Mon: invocation models and retries; Tue: SQS with Lambda, partial batch failure, DLQs; Wed: idempotency; Thu: timeouts, retries and backoff with jitter)

## Scenario

Tenants upload documents to `s3://tidewater-kb-docs-111122223333/tenants/<tenant_id>/docs/`. An
EventBridge rule (source `aws.s3`, detail-type `Object Created`) sends each event to an SQS queue
with a redrive policy to a DLQ; a Lambda with an SQS event source mapping and
`ReportBatchItemFailures` starts a Bedrock Knowledge Base sync for the tenant's data source.

The pilot version started a sync per message with no bookkeeping. Corvid Logistics uploaded 400
files on Monday: duplicate deliveries started duplicate syncs, `ConflictException` (a sync already
running) failed whole batches so good messages were redelivered with bad ones, and one malformed
test message cycled until the DLQ caught it four hours later. You rebuild the handler.

## Why every layer can deliver twice

S3 event notifications, EventBridge and SQS standard queues are all at-least-once. A Lambda can also
time out after `StartIngestionJob` succeeded but before it recorded that, and SQS will redeliver the
message after the visibility timeout. So the handler must be idempotent end to end: a record written
with a condition before the side effect, and a `clientToken` on the side effect itself so a retried
call cannot start a second job.

## Timeouts, retries and backoff with jitter (read this before you code)

- **Bound every wait.** The Lambda timeout must be shorter than the queue's visibility timeout (AWS
  recommends at least six times the function timeout for the visibility timeout), or a message
  becomes visible again while the first invocation is still working on it.
- **One retry layer.** SDK retries (botocore standard or adaptive mode) handle transient errors
  inside one invocation. Do not add an application loop on top: attempts multiply (see w1-t1).
  Across invocations, SQS redelivery is the retry, with `maxReceiveCount` on the redrive policy as the
  budget and the DLQ as the end.
- **Exponential backoff with full jitter** spreads retries so clients do not hammer a throttled
  service in lockstep: sleep a random time between 0 and min(cap, base * 2^attempt). On SQS you get
  backoff by leaving a failed message invisible for its visibility timeout (or by changing it per
  message); `ConflictException` from `StartIngestionJob` is exactly the case where waiting helps.
- **Retry only what can succeed later.** Throttling, conflicts and 5xx: yes. A message that can never
  succeed (bad JSON, a key outside the tenant prefix, an unknown tenant) is a poison message: record
  it and drop it, do not let it consume `maxReceiveCount` deliveries and hide in the DLQ.

## What you have

| Path | What it is |
|---|---|
| `ingest/config.json` | bucket, table, the error codes treated as retryable |
| `ingest/handler.py` | `parse`, `job_key`, `client_token`, `process`, `handler` - **your work**; `Poison`, `ObjectCreated`, `_tenant` are done |
| `tests/x1_support.py` | moto table with tenant profiles (`pk=TENANT#<t>`, `sk=PROFILE`), a `bedrock-agent` client with a Stubber, event builders that match the S3 EventBridge event shape |

## Your task

1. `parse(body, bucket)`: the SQS body is the EventBridge event. Raise `Poison` for anything that
   can never succeed: bad JSON, not an S3 `Object Created` event, another bucket, missing
   key/etag/sequencer, a key outside `tenants/<tenant>/docs/` (including `..` segments) or a
   `.metadata.json` sidecar (the sidecar is ingested with its document).
2. `job_key()` and `client_token()`: one job record per object **version** (the `sequencer`) in the
   tenant's partition; a deterministic token of 33-256 characters.
3. `process()`: tenant must exist in the registry with `status: active` (else `Poison`). Conditional
   put of a `PENDING` record, then `StartIngestionJob` with the tenant's KB and data source and the
   token, then mark `STARTED` with the job id. A duplicate of a `STARTED` record returns `"duplicate"`
   without calling Bedrock; a `PENDING` record left by an earlier failed attempt is finished.
4. `handler()`: per record; return `batchItemFailures` with only the records to redeliver (any AWS
   error, retryable or not, so the DLQ eventually holds the real failures). Poison is logged, recorded
   under `pk=POISON`, `sk=MSG#<messageId>`, and not redelivered.
5. Fill in `ANSWER.md`, including the queue and event source mapping settings you would deploy.

## Acceptance criteria (what the grader checks)

- The same event delivered three times gives one job record and one `StartIngestionJob` call.
- A new object version is a new job; the token is stable per version and differs between versions.
- In a mixed batch only the failed record is reported; a conflict followed by a retry finishes the job.
- Every kind of poison is recorded, not redelivered, and starts nothing; tenants come only from the
  validated key prefix and the registry.

## How to run

```bash
make setup
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade awsfde/x-1
make clean
```
