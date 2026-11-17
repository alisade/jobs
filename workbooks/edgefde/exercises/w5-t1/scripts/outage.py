"""Replay 2026-11-04 at Dunmore: a WAN outage 09:00-12:00, then a flaky link until 14:00.

    python scripts/outage.py incident    writes incident/{gateway.log, dashboard.csv, ntp.log, summary.txt}
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gateway.buffer import Buffer  # noqa: E402
from gateway.cloud import IngestServer, Uplink  # noqa: E402

DEVICES = ["pump-01", "pump-02", "pump-03", "pump-04"]
DAY = datetime(2026, 11, 4, tzinfo=timezone.utc)
CURRENT = [DAY]


def windows():
    for i in range(288):  # 5-minute windows
        yield i, DAY + timedelta(minutes=5 * i)


def run_day(db: Path, outage=(108, 144), flaky=(144, 168), ack_loss=0.7, partial_loss=0.15,
            max_per_request=1000, restart_at: int | None = None, seed: int = 4) -> dict:
    server = IngestServer(max_per_request=max_per_request)
    link = Uplink(server, seed=seed)
    buf = Buffer(db)
    truth: dict[str, int] = {d: 0 for d in DEVICES}
    truth_hour: dict[tuple[str, str], int] = {}
    for i, ts in windows():
        CURRENT[0] = ts
        link.up = not (outage[0] <= i < outage[1])
        flaky_now = flaky[0] <= i < flaky[1]
        link.ack_loss = ack_loss if flaky_now else 0.0
        link.partial_loss = partial_loss if flaky_now else 0.0
        for d_i, dev in enumerate(DEVICES):
            buf.capture(dev, ts.strftime("%Y-%m-%dT%H:%M:%SZ"), "features", {"rms": 0.5 + 0.01 * d_i})
            truth[dev] += 1
            hk = (dev, ts.strftime("%H"))
            truth_hour[hk] = truth_hour.get(hk, 0) + 1
            if (i + d_i) % 9 == 0:
                buf.capture(dev, ts.strftime("%Y-%m-%dT%H:%M:%SZ"), "alert", {"score": 0.91})
                truth[dev] += 1
                truth_hour[hk] += 1
        if restart_at is not None and i == restart_at:
            buf.close()
            buf = Buffer(db)
        buf.replay(link, batch=50, max_batches=20)
    link.up, link.ack_loss, link.partial_loss = True, 0.0, 0.0
    buf.replay(link, batch=50, max_batches=10_000)
    res = {"truth": truth, "server": server.counts(), "received": server.received, "pending": buf.pending_count(),
           "dropped": buf.dropped(), "server_obj": server, "truth_hour": truth_hour}
    buf.close()
    return res


def main(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    db = out / "buffer.db"
    for p in (db, Path(str(db) + "-wal"), Path(str(db) + "-shm")):
        p.unlink(missing_ok=True)
    lines: list[str] = []

    class H(logging.Handler):
        def emit(self, r):
            lines.append(f"{CURRENT[0].strftime('%Y-%m-%dT%H:%M:%S')} {r.levelname:5} {r.name}: {r.getMessage()}")

    logging.getLogger().handlers = [H()]
    logging.getLogger().setLevel(logging.INFO)
    res = run_day(db)
    (out / "gateway.log").write_text("\n".join(lines) + "\n")
    (out / "ntp.log").write_text(
        "2026-11-04T09:00:12 WARN  ntp: no response from 10.20.0.5 (plant NTP via WAN), keeping local clock\n"
        "2026-11-04T10:30:12 WARN  ntp: clock drift estimate +1.1 s since last sync\n"
        "2026-11-04T11:55:12 WARN  ntp: clock drift estimate +2.4 s since last sync\n"
        "2026-11-04T12:00:40 INFO  ntp: synced to 10.20.0.5, stepped clock by -2.43 s\n"
    )
    cloud_hour: dict[tuple[str, str], int] = {}
    for e in res["server_obj"].events.values():
        k = (e["device_id"], e["window_start"][11:13])
        cloud_hour[k] = cloud_hour.get(k, 0) + 1
    with (out / "dashboard.csv").open("w") as fh:
        fh.write("device_id,hour_utc,events_in_cloud,events_captured_on_gateway\n")
        for (d, h), n in sorted(res["truth_hour"].items()):
            fh.write(f"{d},{h},{cloud_hour.get((d, h), 0)},{n}\n")
    (out / "summary.txt").write_text(
        f"cloud stored {sum(res['server'].values())} events, gateway captured {sum(res['truth'].values())}, "
        f"ingest requests carried {res['received']} events, still pending on gateway {res['pending']}, dropped {res['dropped']}\n")
    print((out / "summary.txt").read_text(), end="")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "incident"))
