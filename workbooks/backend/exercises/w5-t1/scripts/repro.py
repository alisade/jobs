#!/usr/bin/env python3
"""Replay INC-6120 against YOUR code: 500 outbox rows, relay-a killed mid-batch, relay-b takes over."""

from __future__ import annotations

import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from outbox.broker import Broker  # noqa: E402
from outbox.consumer import Consumer  # noqa: E402
from outbox.db import add_stage_changes, connect, init_outbox  # noqa: E402
from outbox.relay import Relay, SimulatedCrash  # noqa: E402


class Clock:
    t = 10_000.0

    def __call__(self):
        return self.t


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db, cdb, broker, clock = f"{tmp}/pipeline.db", f"{tmp}/timeline.db", Broker(partitions=12), Clock()
        init_outbox(db)
        add_stage_changes(db, 500, opportunities=400)
        a = Relay(db, broker, "relay-a", clock, batch_size=500, lease_seconds=30)
        try:
            a.run_once(crash_after=212)
        except SimulatedCrash as exc:
            print(f"relay-a: {exc}")
        clock.t += 31
        b = Relay(db, broker, "relay-b", clock, batch_size=500, lease_seconds=30)
        while b.run_once():
            pass
        c = Consumer(cdb, broker)
        c.poll()
        conn = connect(cdb)
        applied = conn.execute("SELECT count(*) FROM stage_changes").fetchone()[0]
        dup = conn.execute("SELECT count(*) FROM (SELECT opportunity_id, version FROM stage_changes "
                           "GROUP BY 1, 2 HAVING count(*) > 1)").fetchone()[0]
        print(f"outbox rows=500 published={len(broker.all_messages())} consumer applied={applied} "
              f"skipped_duplicates={c.skipped} duplicated stage changes={dup}")


if __name__ == "__main__":
    main()
