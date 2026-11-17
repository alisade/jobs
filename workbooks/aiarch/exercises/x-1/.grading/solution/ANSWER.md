# ANSWER: aiarch/x-1

## Approach

Metrics first, then the table definition and the status counts, then the code.

## Root cause

The GSI `by-status` has partition key `status`, and every open session has `status = ACTIVE`,
so all index writes go to one GSI partition key, which DynamoDB serves from one partition
(about 1,000 write units per second). At the 09:00 sign-in wave the index throttles:
`WriteThrottleEvents` with `GlobalSecondaryIndexName=by-status` spikes while the table's own
consumed writes stay modest. GSI throttling back-pressures the base table, so `PutItem` on the
table fails with ThrottlingException even though the table is on-demand. Closed sessions also
stayed in the index under status CLOSED, adding write traffic.

On-demand removes capacity planning, not per-partition limits; provisioned capacity or warm
throughput would not spread one key value across partitions, so neither would have helped.

## Fix

Write-sharded, sparse index key: `active_shard = ACTIVE#<sha256(session_id) mod 10>`, removed on
close. `list_active` queries all ten shards with pagination and merges. Verified with make test.

## Trade-offs / what I would do in production

- Ten shards cost ten queries per "list active"; fine for a runbook and a dashboard, size the
  shard count to peak write rate.
- Changing a GSI key on a live table means adding a new GSI, backfilling, switching readers,
  then dropping the old one.
- Turn on CloudWatch Contributor Insights for the table to see hot keys directly.
