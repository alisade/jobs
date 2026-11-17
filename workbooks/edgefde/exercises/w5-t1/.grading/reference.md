# Reference: edgefde/w5-t1

Root cause: `Buffer.replay` builds each event with `event_id = str(uuid.uuid4())` at send time. The
uplink's `AckTimeout` happens after the server stored the batch; the buffer keeps the rows unsent
and the next attempt rebuilds the batch with new random ids, so the idempotent ingest stores the same
readings again. The flaky period (12:00-14:00) lost about 70% of responses while draining the 09:00-12:00
backlog, so those hours show up two to three times. The summary line proves it: the ingest API
received 1637 events and stored 1637, so it never saw a repeated id even though batches were resent.

Second defect, same function: after a successful call every row of the batch is marked sent, ignoring
the list of acknowledged ids; with a per-request limit the rest of the batch is silently lost.

Red herring: NTP drift and the clock step change wall-clock timestamps on log lines, not the
`window_start` captured with each reading, and the ids were random regardless.

Fix (`.grading/solution/gateway/buffer.py`): `event_id = device/window_start/kind` stored at capture
(`UNIQUE`, `INSERT OR IGNORE` so a re-emitted reading is one event), batches resend the stored ids,
rows are marked sent per acknowledged id inside a transaction. Order (by rowid) and the cap are unchanged.

Cleanup: dedupe the cloud table for 2026-11-04 on (device, window_start, kind); with the planner,
cancel work orders created from duplicate alerts; add a per device-hour reconciliation (gateway
counts are sent as a daily summary) with an alert on mismatch; size the buffer for the next outage.
