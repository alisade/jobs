"""Replay 2026-10-20 through the sink with the restarts the supervisor did that day.

    python scripts/simulate.py incident     writes incident/{sink.log, broker.log, window_counts.csv, summary.txt}

Restarts: about 08:04 OOM kill, 15:28 deploy (rolling restart), 23:45 OOM kill. A restart
throws the Sink object away (its in-memory state is gone) and builds a new one,
exactly like a process restart.
"""

from __future__ import annotations

import importlib
import json
import logging
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sink.broker import FakeBroker  # noqa: E402
from sink.store import WindowStore  # noqa: E402

DEVICES = [f"pump-{i:02d}" for i in range(1, 7)]
DAY = datetime(2026, 10, 20, tzinfo=timezone.utc)
RESTARTS = {37: "OOMKilled (exit 137)", 71: "deploy sink:2026.10.20-1", 109: "OOMKilled (exit 137)"}
MAX_RECORDS = 80
CURRENT_POLL = 0


class Killed(Exception):
    """Raised by a test hook to model the process dying at an exact point."""


def produce_day(b: FakeBroker, topic: str) -> int:
    rng = random.Random(20)
    n = 0
    for i in range(1440):
        ts = (DAY + timedelta(minutes=i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        for dev in DEVICES:
            rec = {"device_id": dev, "window_start": ts, "rms": round(rng.uniform(0.2, 1.4), 4), "seq": i}
            b.produce(topic, dev.encode(), json.dumps(rec).encode())
            n += 1
    return n


def run_scenario(db_path: Path, restarts: dict[int, str] | None = None, store_wrapper=None, log=None) -> dict:
    consumer_mod = importlib.import_module("sink.consumer")
    restarts = RESTARTS if restarts is None else restarts
    b = FakeBroker()
    b.create_topic(consumer_mod.TOPIC, 3)
    produced = produce_day(b, consumer_mod.TOPIC)
    store = WindowStore(db_path)
    target = store_wrapper(store) if store_wrapper else store

    def new_sink():
        return consumer_mod.Sink(b, target)

    sink = new_sink()
    polls = 0
    global CURRENT_POLL
    events = []
    for _ in range(10_000):
        polls += 1
        CURRENT_POLL = polls
        if polls in restarts:
            committed = sum(b.committed(consumer_mod.GROUP, consumer_mod.TOPIC).values())
            events.append((polls, restarts[polls], committed))
            if log:
                log(f"supervisor: sink process restarted: {restarts[polls]} (rows in dashboard table: {store.count()})")
            sink = new_sink()
        try:
            got = sink.step(MAX_RECORDS)
        except Killed:
            events.append((polls, "killed by hook", 0))
            sink = new_sink()
            continue
        if got == 0 and b.lag(consumer_mod.GROUP, consumer_mod.TOPIC) == 0 and not getattr(sink, "buffer", []):
            break
        if got == 0 and b.lag(consumer_mod.GROUP, consumer_mod.TOPIC) > 0:
            # nothing left to poll in this instance but work uncommitted: a real consumer would idle; restart cleanly
            sink = new_sink()
    return {
        "produced": produced,
        "rows": store.count(),
        "distinct": store.distinct(),
        "lag": b.lag(consumer_mod.GROUP, consumer_mod.TOPIC),
        "commit_calls": b.commit_calls,
        "transactions": store.transactions,
        "events": events,
        "per_device_hour": store.per_device_hour(),
        "store": store,
    }


def main(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    db = out / "dashboard.db"
    if db.exists():
        db.unlink()
    lines: list[str] = []

    def stamp() -> str:
        # the replay compresses the day: one poll is about 13 minutes of plant time
        t = DAY + timedelta(seconds=CURRENT_POLL * 785)
        return t.strftime("%Y-%m-%dT%H:%M:%S")

    class H(logging.Handler):
        def emit(self, record):
            lines.append(f"{stamp()} {record.levelname:5} {record.name}: {record.getMessage()}")

    root = logging.getLogger()
    root.handlers = [H()]
    root.setLevel(logging.INFO)
    logging.getLogger("broker").setLevel(logging.INFO)
    res = run_scenario(db, log=lambda m: lines.append(f"{stamp()} WARN  {m}"))
    out_lines = []
    for i, ln in enumerate(lines):
        out_lines.append(ln)
        if i % 23 == 11:
            out_lines.append(f"{ln[:19]} WARN  sink: consumer lag 4{i % 7}21 above alert threshold 2000 (group dashboard-sink)")
    lines = out_lines
    (out / "sink.log").write_text("\n".join(lines) + "\n")
    (out / "broker.log").write_text(
        "2026-10-20T05:58:11 WARN  [ReplicaManager broker=2] Partition vibration.features-1 is under-replicated (ISR 2/3)\n"
        "2026-10-20T06:04:40 INFO  [ReplicaManager broker=2] Partition vibration.features-1 ISR expanded to 3/3\n"
        "2026-10-20T11:39:58 INFO  [GroupCoordinator] Member sink-7f9c left group dashboard-sink (consumer.close)\n"
        "2026-10-20T11:40:09 INFO  [GroupCoordinator] Rebalance complete for group dashboard-sink, generation 14\n"
        "2026-10-20T17:04:52 INFO  [GroupCoordinator] Member sink-3a01 session timeout, removing from group dashboard-sink\n"
    )
    with (out / "window_counts.csv").open("w") as fh:
        fh.write("device_id,hour,windows,expected\n")
        for dev, hour, n in res["per_device_hour"]:
            fh.write(f"{dev},{hour},{n},60\n")
    short = [(d, h, n) for d, h, n in res["per_device_hour"] if n != 60]
    (out / "summary.txt").write_text(
        f"produced={res['produced']} rows_in_dashboard={res['rows']} distinct_windows={res['distinct']} "
        f"consumer_lag_at_end={res['lag']}\nhours with != 60 windows: {len(short)}\n"
        + "".join(f"  {d} {h}:00 -> {n}\n" for d, h, n in short[:40])
    )
    print((out / "summary.txt").read_text(), end="")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "incident"))
