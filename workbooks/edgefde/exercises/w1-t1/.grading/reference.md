# Reference: edgefde/w1-t1

## Root cause

`Sink` creates its consumer with `enable_auto_commit=True`. With auto-commit, every `poll()` first
commits the positions reached by the previous poll. The sink buffers records in memory and only
writes them every 5 polls, so at any moment the committed offsets are up to 4 polls (320 records)
ahead of what is in SQLite. When the process dies (OOM kill, deploy), the buffer is gone and the new
consumer starts from the committed offsets: the buffered records are never delivered again.

Evidence in `incident/sink.log`:

- first OOM: last auto-commit sum=2800, rows in table 2800: nothing lost (restart right after a flush)
- deploy: last auto-commit sum=5440, rows in table 5200: 240 lost
- last OOM: last auto-commit sum=8400, rows in table 8000: 400 lost in total, 160 more
- `summary.txt`: produced=8640, rows=8240, 400 missing

Why the hours differ per pump: crc32 puts pumps 01/02/05/06 on partition 0 and 03/04 on partition 2
(partition 1 is empty). Polling is round-robin per record across partitions, so partition 0 (four
devices) falls further behind in event time; a restart therefore drops older event hours (10:00-11:00)
for partition 0 devices and later ones (21:00-22:00) for partition 2.

Red herrings: the under-replicated `vibration.features-1` recovered within minutes and partition 1
holds no data; replication health affects durability on the broker, not what this consumer commits.
The lag warnings are real (the sink is behind) but lag never drops data by itself; it only explains
why lost event hours trail the restart times.

## Fix

`.grading/solution/sink/consumer.py`: `enable_auto_commit=False` and `self.consumer.commit()` right
after `store.write_rows(...)` returns. `.grading/solution/sink/store.py`: primary key on
`(device_id, window_start)` and `ON CONFLICT ... DO UPDATE`, so a crash between the write and the
commit only causes a redelivery that overwrites identical rows. Batching is unchanged.

## Recovery

Stop the sink, reset the group's offsets to the start of 2026-10-20
(`kafka-consumer-groups --group dashboard-sink --reset-offsets --to-datetime 2026-10-20T00:00:00.000
--topic vibration.features --execute`) if retention still covers it, or run the backfill from the
archive; both are safe only because the write is now idempotent. Then compare produced vs stored
windows per device-hour and alert on that check going forward.
