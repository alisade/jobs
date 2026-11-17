# ANSWER: awsfde/x-1 Idempotent document-ingestion Lambda

## Approach

Duplicates come from S3, EventBridge and SQS (at least once) and from timeouts after the side effect.
A conditional PENDING record before StartIngestionJob and a clientToken derived from the object
version make every crash point safe.

## Fix

Implemented parse, job_key, client_token, process and handler. Poison messages are recorded under
POISON with the reason and acknowledged; AWS errors are reported per record.

## Trade-offs / what I would do in production

Event source mapping with ReportBatchItemFailures, batch size 10, maximum concurrency 5; visibility
timeout six times the function timeout; maxReceiveCount 5 with a DLQ alarm and a redrive runbook.
Because a data source runs one sync at a time, coalesce bulk uploads per tenant. TTL on job records.
