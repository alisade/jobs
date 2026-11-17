# Rubric: backend/w5-c1 Idempotent timeline consumer in Go
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Idempotency design | 15 | Full: dedupe record written in the same transaction as the mutation, version guard on every change, tombstones keep versions, counter derived from live-before vs live-after rather than incremented per event type. Partial: dedupe table only, or version guard only (one of duplicates / reordering still unsafe). Zero: dedupe in a process-local map. |
| 3 | Delivery semantics | 15 | Full: commit strictly after handling; poison parked immediately; bounded retries with backoff then DLQ with attempts and reason; failed commit stops the loop; nothing blocks a partition. Partial: correct order but retries forever or drops poison silently. |
| 4 | Go quality and shutdown | 10 | Context used correctly (shutdown does not abort the in-flight transaction, e.g. context.WithoutCancel or a separate work context), no goroutine leaks, errors wrapped with %w and context, small readable functions, go vet clean. |
| 5 | ANSWER.md | 10 | Explains why the dedupe row and the mutation must commit together (crash windows on both sides), at-least-once vs effectively-once, and at least two production items with a position (processed-table retention or natural idempotency, DLQ replay and alerting, lag metrics, rebalance handling, ordering vs parallelism). |
Total: 100
