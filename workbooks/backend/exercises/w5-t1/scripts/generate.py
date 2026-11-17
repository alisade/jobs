#!/usr/bin/env python3
"""Generate the incident bundle for backend/w5-t1 into <out>/ (deterministic, stdlib only)."""

from __future__ import annotations

import pathlib
import random
import sys
import uuid

FIRST, BATCH, PUBLISHED_BEFORE_KILL = 18201, 500, 212


def u(rng: random.Random) -> str:
    return str(uuid.UUID(int=rng.getrandbits(128), version=4))


def main(out: str) -> None:
    o = pathlib.Path(out)
    o.mkdir(parents=True, exist_ok=True)
    rng = random.Random(1110)
    rows = []
    for i in range(BATCH):
        rid = FIRST + i
        rows.append({"id": rid, "event_id": u(rng), "opp": f"opp-{rng.randint(1, 900):04d}", "ver": rng.randint(2, 9)})

    a = ["2026-11-10T14:01:58.204Z INFO  relay-a pod=outbox-relay-7c9f-ab12 version=1.8.1 batch_size=500 lease=30s",
         f"2026-11-10T14:01:58.311Z INFO  relay-a claimed 500 rows ids={FIRST}..{FIRST + BATCH - 1} lease_until=14:02:28.311Z"]
    for i, r in enumerate(rows[:PUBLISHED_BEFORE_KILL]):
        if i % 40 == 0 or i == PUBLISHED_BEFORE_KILL - 1:
            a.append(f"2026-11-10T14:02:{2 + i // 20:02d}.{rng.randint(100, 999)}Z DEBUG relay-a published outbox_id={r['id']} "
                     f"key={r['opp']} message_event_id={u(rng)} partition={rng.randint(0, 11)} produce_ms={rng.randint(400, 1900)}")
    a += ["2026-11-10T14:02:11.004Z INFO  relay-a received SIGTERM (rollout outbox-relay 1.8.2), finishing current batch",
          "2026-11-10T14:02:30.518Z WARN  relay-a produce latency high p99=1.8s, batch 212/500",
          "2026-11-10T14:02:41.009Z ---- container killed: terminationGracePeriodSeconds=30 exceeded (exit 137)"]
    (o / "relay-a.log").write_text("\n".join(a) + "\n")

    b = ["2026-11-10T14:02:31.877Z INFO  relay-b pod=outbox-relay-55d1-cd34 version=1.8.2 batch_size=500 lease=30s",
         f"2026-11-10T14:02:42.120Z INFO  relay-b claimed 500 rows ids={FIRST}..{FIRST + BATCH - 1} (lease expired, previous owner relay-a)"]
    for i, r in enumerate(rows):
        if i % 50 == 0:
            b.append(f"2026-11-10T14:02:{43 + i // 60:02d}.{rng.randint(100, 999)}Z DEBUG relay-b published outbox_id={r['id']} "
                     f"key={r['opp']} message_event_id={u(rng)} partition={rng.randint(0, 11)} produce_ms={rng.randint(8, 30)}")
    b.append(f"2026-11-10T14:02:52.340Z INFO  relay-b marked 500 rows sent ids={FIRST}..{FIRST + BATCH - 1}")
    (o / "relay-b.log").write_text("\n".join(b) + "\n")

    c = ["# timeline-consumer, group timeline-consumer, processed-event dedupe on header event_id"]
    for r in rows[:6]:
        e1, e2 = u(rng), u(rng)
        c.append(f"2026-11-10T14:02:0{rng.randint(3, 9)}Z INFO  applied OpportunityStageChanged opp={r['opp']} version={r['ver']} event_id={e1}")
        c.append(f"2026-11-10T14:02:4{rng.randint(4, 9)}Z INFO  applied OpportunityStageChanged opp={r['opp']} version={r['ver']} event_id={e2}")
    c += ["2026-11-10T14:03:10Z INFO  dedupe stats last 5m: received=712 applied=712 skipped_duplicates=0",
          "2026-11-10T14:05:00Z WARN  notifications-svc: deal desk emails sent twice for 212 opportunity stage changes"]
    (o / "consumer.log").write_text("\n".join(c) + "\n")

    dump = ["id,event_id,aggregate_id,status,claimed_by,sent_at"]
    for r in rows[:12]:
        dump.append(f"{r['id']},{r['event_id']},{r['opp']},sent,relay-b,2026-11-10T14:02:52Z")
    dump.append("... 488 more rows, all status=sent claimed_by=relay-b")
    (o / "outbox-dump.csv").write_text("\n".join(dump) + "\n")

    (o / "broker-metrics.txt").write_text("""# Redpanda cluster keystone-events, 2026-11-10 (1-minute buckets)
time   produce_p99_ms  consumer_lag(timeline-consumer)  under_replicated
14:00  21              0                                0
14:01  640             12                               0
14:02  1840            498                              1   # broker-2 rolling restart (planned maintenance)
14:03  33              0                                0
14:04  19              0                                0
""")
    (o / "PAGER.md").write_text(f"""# INC-6120: duplicate stage changes on opportunity timelines

**Opened:** 2026-11-10 14:07 by Dana Whitfield (sales ops) | **On call:** Marcus Oyelaran

Since about 14:02 the activity timeline shows some stage changes twice (same version, a few seconds
apart), and the deal desk received two emails for 212 opportunity moves. The consumer team says their
dedupe is on and "it cannot be us, we dedupe on event_id". The broker team had a planned rolling
restart of broker-2 at 14:02 and produce latency spiked.

What happened around that time:
- 14:02 outbox-relay rollout 1.8.1 -> 1.8.2 (no code change in the publish path, only a dependency bump).
- 14:02 broker-2 restart (planned).

Attached: relay-a.log (old pod), relay-b.log (new pod), consumer.log, outbox-dump.csv, broker-metrics.txt.
Code: `outbox/relay.py`, `outbox/consumer.py`, `outbox/broker.py`, `outbox/db.py`.
""")
    print(f"bundle written to {o}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "incident")
