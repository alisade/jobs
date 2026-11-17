# Reference: awsfde/x-1

Solution: `.grading/solution/ingest/handler.py`.

- **Key:** `pk=TENANT#<t>`, `sk=INGEST#<sha256(key)[:16]>#<sequencer>`: one record per object version
  in the tenant partition. The sequencer (from the S3 event) orders versions of the same key.
- **Order of operations:** conditional put PENDING, StartIngestionJob with
  `clientToken=sha256(tenant|key|sequencer)`, update to STARTED. A crash after the call leaves PENDING;
  the redelivery re-sends the same token, so Bedrock does not start a second job.
- **Failures:** poison (never succeeds) is recorded under `POISON` and acknowledged; any ClientError is
  reported in `batchItemFailures` so SQS redelivers only that record, and repeated failures land in
  the DLQ after `maxReceiveCount`.
- **At scale:** a data source runs one sync at a time, so per-object jobs mostly conflict during bulk
  uploads. Coalesce per tenant: debounce with a short delay or a Step Functions wait, then one sync.
