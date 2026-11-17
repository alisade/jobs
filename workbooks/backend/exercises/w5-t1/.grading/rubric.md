# Rubric: backend/w5-t1 Duplicate stage-change events after the relay restart
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 35 | points = 35 * passed / total from grade.sh |
| 2 | Root cause | 25 | Full: the relay regenerates `event_id` (uuid4) at publish time instead of carrying the outbox row's id, so consumer dedupe cannot match redeliveries; states that the redelivery itself (kill mid-batch, lease expiry, new pod republishes) is expected at-least-once behavior. Partial: "the relay published twice" without the identity mechanism. Zero: blames the consumer dedupe or the broker. |
| 3 | Evidence | 20 | Quotes the differing message ids for the same outbox_id across relay-a/relay-b and the dump, the consumer's skipped_duplicates=0 with applied=712, the kill after the grace period, the lease-expired reclaim, and make repro numbers before/after. Partial: one or two. |
| 4 | Secondary defects and red herring | 10 | Mark-sent only at end of batch, non-atomic claim and no ownership check; explains why the broker restart/latency is a trigger, not the cause. |
| 5 | Fix quality | 5 | Stable id, conditional claim with RETURNING, per-row sent with ownership, stop on lost lease; no attempt to promise exactly-once from the relay. |
| 6 | Production follow-up | 5 | Batch size vs grace period, lease renewal, event-id contract, CDC option, alerts. |
Total: 100
