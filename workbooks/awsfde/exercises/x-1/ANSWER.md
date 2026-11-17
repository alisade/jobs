# ANSWER: awsfde/x-1 Idempotent document-ingestion Lambda

## Approach

<!-- Where duplicates come from, and how the conditional write plus the clientToken make the
handler safe at each point it can crash. -->

## Fix

<!-- What you implemented; your poison policy and why. -->

## Trade-offs / what I would do in production

<!-- Event source mapping (batch size, batching window, ReportBatchItemFailures, maximum
concurrency), visibility timeout vs function timeout, maxReceiveCount and the DLQ alarm, redrive.
One sync per data source runs at a time: would you coalesce uploads (debounce per tenant) instead
of one job per object? TTL on job records; Powertools idempotency as an alternative. -->
