# Rubric: edgefde/w1-t1 Gaps in window counts after every consumer restart
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 35 | points = 35 * passed / total from grade.sh |
| 2 | Root cause | 25 | Full: enable.auto.commit commits the positions of the previous poll at the next poll, while records sit in the in-memory buffer until the flush every 5 polls, so a restart loses everything polled but not flushed; offsets were already committed past it, so it is never redelivered. Partial: "commit before write" without the buffer/auto-commit mechanism. Zero: blames the broker, the OOM itself or lag. |
| 3 | Evidence | 15 | Quotes the restart lines with rows in the table against the auto-commit sum just before: deploy 5440 committed vs 5200 rows (240 lost), last OOM 8400 vs 8000 (160 more, 400 in total = summary.txt), first OOM 2800 vs 2800 (nothing lost: it hit right after a flush). Explains the hours: pumps 01/02/05/06 share partition 0 and pumps 03/04 partition 2 (crc32 of the key); round-robin polling leaves partition 0 further behind, so the same restart drops older event hours for partition 0 devices. |
| 4 | Red herrings | 10 | Under-replicated vibration.features-1 recovered at 06:04 and partition 1 carries no device data at all; the lag warnings show the sink was behind (which is why lost event hours trail the restart times) but lag never loses data by itself. |
| 5 | Fix quality | 10 | Auto-commit off, commit right after the durable write, idempotent write (PK + upsert) for the kill-after-write window, batching kept. |
| 6 | Recovery and prevention | 5 | Recover 2026-10-20 by resetting the group's offsets to a timestamp (kafka-consumer-groups --reset-offsets --to-datetime) or a backfill from the archive, relying on the idempotent write; alert on produced vs stored counts per device-hour. |
Total: 100
