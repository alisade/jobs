# backend/w5-t1 - Duplicate stage-change events after the relay restart

**Type:** troubleshooting | **Estimate:** 2 hours | **Study plan:** Week 5 (Tue: transactional outbox; Wed: idempotent consumers)

## Scenario

pipeline-svc writes an outbox row in the same transaction as every opportunity stage change. Two
replicas of `outbox-relay` publish those rows to the `pipeline.events` topic, and `timeline-consumer`
applies them to the activity timeline, deduplicating on the message's `event_id`. On 2026-11-10 at
14:02 the relay was rolled out and broker-2 had a planned restart in the same minute. Since then sales
ops sees doubled stage changes and the deal desk got two emails for 212 opportunity moves. The pager
is INC-6120; you are the engineer who owns the relay.

## What you have

| Path | What it is |
|---|---|
| `incident/PAGER.md` | the incident summary (created by `make setup`) |
| `incident/relay-a.log`, `incident/relay-b.log` | the old and the new relay pod |
| `incident/consumer.log` | timeline-consumer around the incident |
| `incident/outbox-dump.csv` | the outbox rows of the affected batch |
| `incident/broker-metrics.txt` | produce latency and consumer lag |
| `outbox/` | `relay.py` (the relay), `consumer.py`, `broker.py` (in-process Kafka stand-in), `db.py` (SQLite outbox) |
| `scripts/repro.py` | `make repro`: replays the incident against your code |

## Your task

1. Find the root cause and back it with evidence from the bundle and from `make repro`.
2. Decide which part of what happened is expected (at-least-once delivery) and which is a defect.
3. Fix `outbox/relay.py` so that:
   - each message carries the identity of the outbox row it came from, so downstream dedupe works;
   - claiming is atomic (two replicas never hold a live claim on the same row);
   - each row is marked sent as soon as it is published, and only by the relay that still owns it,
     so a crash republishes at most the in-flight row and a relay whose lease expired stops.
   Keep `Relay`'s public methods (`claim`, `publish_claimed`, `run_once`) and constructor.
4. Fill in `ANSWER.md`.

## Acceptance criteria (what the grader checks)

- Crash mid-batch, restart, consume: every stage change applied exactly once.
- Published message `event_id` headers equal the outbox `event_id`s.
- After a crash at most one row is published twice by the relays.
- A live claim cannot be taken by the other replica; a relay that lost its lease does not publish.
- Per-opportunity order is preserved; consumer dedupe still works.
- `ANSWER.md` root cause and evidence carry most of the points.

## How to run

```bash
make setup      # venv + incident bundle
make repro      # outbox rows, published, applied, duplicated stage changes
make test       # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade backend/w5-t1
make clean
```
