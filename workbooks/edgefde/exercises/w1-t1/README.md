# edgefde/w1-t1 - Gaps in window counts after every consumer restart

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 1 (Tue: Kafka as a client author; Wed: delivery semantics)

## Scenario

Monday morning at Corvane Industrial's Dunmore plant (fictional). The reliability lead messages you:

> "The vibration dashboard has holes in Tuesday 2026-10-20: every pump is short somewhere, and pumps
> 03 and 04 only lost windows late in the evening while the others also lost a chunk mid-morning. The
> sink got OOM-killed twice and we deployed it once that day, but it always catches up, and Kafka was
> complaining about an under-replicated partition that morning. Can you tell us what we lost and make
> sure it does not happen again? We are about to train a model on this table."

The sink (`sink/consumer.py`) reads `vibration.features`, enriches each record with an asset tag,
buffers records and writes them to SQLite in batches (the enrichment used to be slow, so batching
was added for throughput). A supervisor restarts it when it dies.

Kafka is an in-process fake (`sink/broker.py`) with real consumer-group semantics, including
`enable.auto.commit`. `make setup` replays 2026-10-20 with the same three restarts and writes the
evidence to `incident/`.

## What you have

| Path | What it is |
|---|---|
| `incident/summary.txt` | produced vs stored windows, hours with gaps |
| `incident/window_counts.csv` | windows per device per hour (expected 60) |
| `incident/sink.log` | sink, broker client and supervisor log for the day |
| `incident/broker.log` | broker-side log lines from that day |
| `sink/consumer.py` | the sink (edit) |
| `sink/store.py` | the SQLite table writer (edit if you need to) |
| `sink/broker.py` | the fake Kafka (do not edit) |
| `scripts/simulate.py` | `make run`: replays the day through the current code (do not edit) |

## Your task

1. Find the root cause of the missing windows. Prove it from `incident/` (quote log lines and numbers),
   and explain why the holes sit at different event hours for pumps 03-04 than for the other pumps.
2. Decide whether the under-replicated partition and the lag warnings matter.
3. Fix the sink so a restart at any point (before the write, after the write, between polls) loses
   nothing and duplicates nothing, without giving up batched writes.
4. Say how you would recover the lost windows for 2026-10-20 in production.

## Acceptance criteria (what the grader checks)

- `make run` over the day with restarts stores exactly 8640 distinct windows and 8640 rows.
- Killing the process right after a write commits, or right before it, still gives 8640 / 8640.
- Committed offsets never run ahead of the rows that are durable in the table.
- Writes stay batched (a few dozen transactions for the day, not one per record).
- `ANSWER.md`: root cause with evidence from the logs, the red herrings ruled out, the recovery plan.

## How to run

```bash
make setup     # venv + incident/
make run       # replay the day through your current code
make test      # visible checks
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade edgefde/w1-t1
make clean
```

## What to submit

Your changes under `sink/` and a filled-in `ANSWER.md`.
