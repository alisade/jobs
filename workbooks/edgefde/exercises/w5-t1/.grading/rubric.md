# Rubric: edgefde/w5-t1 Alert counts tripled after the plant's WAN outage
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 35 | points = 35 * passed / total from grade.sh |
| 2 | Root cause | 25 | Full: `replay` generates a fresh `uuid4()` event_id every time it builds a batch, so after an AckTimeout (server stored the batch, response lost) the retry carries new ids and the idempotent ingest stores every event again; the idempotency key must be fixed at capture. Also: rows are marked sent per batch, ignoring which ids were acknowledged (partial ack loses rows). Partial: "retries cause duplicates" without the id-generation point. |
| 3 | Evidence | 10 | summary.txt: 1637 stored vs 1280 captured, and 1637 received = 1637 stored, i.e. the server never saw a repeated id although batches were resent; dashboard.csv hours 09-13 at 2-3x; "ack timeout ... will retry" lines in the flaky period; the uuid4 call in buffer.py. |
| 4 | Red herring | 10 | The NTP drift (+2.4 s, then a step of -2.43 s) does not create new events: window_start comes from the capture and the ids were random anyway; the inflation follows the ack timeouts, not the clock step. |
| 5 | Fix quality | 10 | Stable event id from (device, window, kind) or a UUID stored at capture; mark sent per acked id in a transaction; INSERT OR IGNORE for re-emitted readings; order and cap kept. |
| 6 | Cleanup and prevention | 10 | Dedupe cloud data by (device, window_start, kind) for 2026-11-04, cancel work orders raised from duplicates with the planner, monitor cloud vs gateway counts per device-hour, size the buffer for the carrier's next outage. |
Total: 100
