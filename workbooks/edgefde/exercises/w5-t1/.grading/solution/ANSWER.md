# ANSWER: edgefde/w5-t1 Alert counts tripled after the WAN outage

## Approach

Compared the cloud and gateway counts first (`summary.txt`, `dashboard.csv`), then read `replay`.

## Root cause

`replay` creates `event_id = uuid4()` every time it builds a batch. During the flaky period the
server stored batches and the response was lost (`AckTimeout`); the rows stayed unsent and the retry
rebuilt them with new random ids, so the idempotent ingest stored them again:

```text
cloud stored 1637 events, gateway captured 1280, ingest requests carried 1637 events
pump-02,13,46,13
```

1637 received and 1637 stored means the server never saw a repeated id even though batches were
resent. The inflation sits in 09:00-13:00, the backlog drained while about 70% of responses were lost.
`replay` also marks the whole batch sent regardless of which ids were acknowledged, which loses rows
on a partial ack. The NTP drift is not involved: `window_start` comes from capture, the clock step
only affects log timestamps, and the ids were random anyway.

## Fix

The event id is fixed at capture from (device, window_start, kind) and stored with a UNIQUE
constraint (`INSERT OR IGNORE` also absorbs a re-emitted reading). Resends carry the stored ids;
rows are marked sent per acknowledged id in one transaction. Verified with `make run` (1280 = 1280),
90% lost acks, partial acks and a restart mid-replay.

## Trade-offs / what I would do in production

Dedupe the cloud data for 2026-11-04 on (device, window_start, kind) and go through the work orders
raised that day with the planner. Send a daily per device-hour count from each gateway and alert when
the cloud disagrees. Size the buffer for the carrier's next outage and alert on buffer fill.
