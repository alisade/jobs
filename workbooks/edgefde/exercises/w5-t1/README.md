# edgefde/w5-t1 - Alert counts tripled after the plant's WAN outage

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 5 (Wed: offline operation, buffering and idempotent replay)

## Scenario

On 2026-11-04 the Dunmore plant (Corvane Industrial, fictional) lost its WAN link from 09:00 to 12:00,
and the carrier's replacement router dropped responses until about 14:00. The gateways kept scoring
locally, as designed, and buffered everything in SQLite. The reliability lead writes:

> "The cloud dashboard shows two to three times the normal number of events for 09:00-13:00 on every
> pump, alerts included. The planners raised work orders off some of those duplicates. The gateway
> log is full of NTP warnings from the outage; did the clock jump make the same windows look new?
> Fix it before the next outage, the carrier says there will be one."

The cloud ingest API stores events by `event_id` and ignores repeats (its documented idempotency
contract). `make setup` replays the day through the gateway buffer and writes the evidence.

## What you have

| Path | What it is |
|---|---|
| `incident/summary.txt` | events stored in the cloud vs captured on the gateway |
| `incident/dashboard.csv` | per device and hour: cloud count vs gateway count |
| `incident/gateway.log` | buffer log for the day |
| `incident/ntp.log` | the NTP warnings |
| `incident/buffer.db` | the gateway's SQLite buffer after the day |
| `gateway/buffer.py` | the store-and-forward buffer (edit) |
| `gateway/cloud.py` | fake ingest API and the lossy uplink (do not edit) |
| `scripts/outage.py` | `make run`: the day through your current code (do not edit) |

## Your task

1. Find why the cloud has more events than the gateway produced. Prove it with numbers from
   `incident/` (the summary line has a telling pair of numbers) and the code.
2. Decide whether the clock drift is involved.
3. Fix the buffer so lost responses, partial acknowledgements, a gateway restart mid-replay and a
   re-emitted reading all end with exactly the gateway's events in the cloud, in order per device,
   with the disk cap still enforced.
4. Say how you would clean up the duplicates already in the cloud and the work orders raised from them.

## Acceptance criteria (what the grader checks)

- The outage day (several seeds, and with 90% lost acks) gives cloud counts equal to the gateway's.
- The server may acknowledge only part of a batch: unacknowledged rows stay pending and are sent later.
- An event keeps the same id on every resend; a restart mid-replay changes nothing; order per device
  is preserved; the buffer cap still drops oldest and counts it.
- `ANSWER.md`: root cause with evidence, why the clock is not it, the cleanup plan.

## How to run

```bash
make setup     # venv + incident/
make run       # replay the day through your current code
make test      # visible checks
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade edgefde/w5-t1
make clean
```

## What to submit

`gateway/buffer.py` and a filled-in `ANSWER.md`.
