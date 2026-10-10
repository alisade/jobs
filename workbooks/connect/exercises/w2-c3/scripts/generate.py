"""Generate the LFG help desk contact dataset (deterministic).

Writes, under the output directory (default data/):
  contact_records.parquet   one row per contact: a flattened contact record (CTR) the LFG Firehose
                            pipeline lands in S3, six weeks 2026-08-24 .. 2026-10-04 (UTC timestamps)
  interval_staffing.csv     staffed agents per half hour (local time) per day
  change_log.csv            the CAB change calendar for the period

Usage: python scripts/generate.py [out_dir]
"""

from __future__ import annotations

import csv
import datetime as dt
import random
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import pyarrow as pa
import pyarrow.parquet as pq

ET = ZoneInfo("America/New_York")
START = dt.date(2026, 8, 24)
DAYS = 42
OKTA_CHANGE = dt.datetime(2026, 9, 21, 6, 0, tzinfo=ET)

DRIVERS = [
    ("password_reset", 0.22, 300), ("mfa_enrollment", 0.08, 360), ("vpn", 0.12, 420),
    ("laptop_hardware", 0.15, 540), ("sap_access", 0.10, 600), ("software_install", 0.18, 480), ("other", 0.15, 420),
]
QUEUE_FOR = {
    "password_reset": "PasswordReset", "mfa_enrollment": "PasswordReset", "vpn": "GeneralSupport",
    "laptop_hardware": "GeneralSupport", "sap_access": "Applications", "software_install": "GeneralSupport", "other": "GeneralSupport",
}

CHANGES = [
    ("CHG0031702", "2026-08-31 21:00", "Connect: publish LFG Help Desk Inbound flow v14 (prompt wording)", "Amazon Connect"),
    ("CHG0031790", "2026-09-14 22:00", "ServiceNow: Xanadu patch 6 upgrade", "ServiceNow"),
    ("CHG0031877", "2026-09-21 06:00", "Okta: SSPR policy - remove SMS factor, require Okta Verify push, enrollment grace 0 days", "Identity"),
    ("CHG0031881", "2026-09-22 20:00", "Connect: routing profile rp-tier1 adds GeneralSupport at priority 2 (delay 10 s)", "Amazon Connect"),
    ("CHG0031934", "2026-09-29 21:00", "Network: Zscaler client 4.6 rollout wave 2", "Network"),
]


def day_volume(d: dt.date, channel: str) -> int:
    weekend = d.weekday() >= 5
    base = {"VOICE": (1100, 120), "CHAT": (450, 40)}[channel][1 if weekend else 0]
    if d == dt.date(2026, 9, 7):  # Labor Day
        base = int(base * 0.15)
    return base


def arrival_minute(r: random.Random, channel: str) -> int:
    # weekday shape: peak 08:00-11:00 local, long tail to 20:00; chat is also open 20:00-24:00
    if channel == "CHAT" and r.random() < 0.08:
        return r.randint(20 * 60, 24 * 60 - 1)
    while True:
        m = int(r.gauss(10.5 * 60, 2.6 * 60))
        if 6 * 60 <= m < 20 * 60:
            return m


def pick_driver(r: random.Random, post: bool) -> str:
    weights = []
    for name, w, _ in DRIVERS:
        if post and name == "password_reset":
            w *= 1.7
        if post and name == "mfa_enrollment":
            w *= 1.5
        weights.append(w)
    return r.choices([d[0] for d in DRIVERS], weights=weights)[0]


def main(out: Path) -> None:
    r = random.Random(20260921)
    out.mkdir(parents=True, exist_ok=True)
    rows: list[tuple] = []
    seq = 0
    end_local = dt.datetime.combine(START + dt.timedelta(days=DAYS), dt.time(0, 0), tzinfo=ET)

    def emit(start_local: dt.datetime, channel: str, employee: str, driver: str, allow_repeat: bool) -> None:
        nonlocal seq
        seq += 1
        post = start_local >= OKTA_CHANGE
        aht = dict((d[0], d[2]) for d in DRIVERS)[driver]
        if post and driver == "password_reset":
            aht = 420
        if channel == "CHAT":
            aht = int(aht * 1.6)
        minute = start_local.hour * 60 + start_local.minute
        week_index = (start_local.date() - START).days // 7
        abandon_p = 0.12 if 8 * 60 <= minute < 10 * 60 else 0.04
        if week_index == 5:  # short-staffed week (training), mild everywhere
            abandon_p += 0.02
        if channel == "CHAT":
            abandon_p *= 0.5
        wait = int(r.expovariate(1 / (55 if abandon_p > 0.1 else 25)))
        abandoned = r.random() < abandon_p
        init = start_local.astimezone(dt.timezone.utc)
        enq = init + dt.timedelta(seconds=r.randint(20, 70) if channel == "VOICE" else r.randint(3, 15))
        if abandoned:
            connected = None
            agent = None
            talk = 0
            acw = 0
            disc = enq + dt.timedelta(seconds=wait)
            reason = "CUSTOMER_DISCONNECT"
            resolution = None
        else:
            connected = enq + dt.timedelta(seconds=wait)
            agent = f"agent{r.randint(1, 120):03d}@lfg.example"
            handle = max(60, int(r.gauss(aht, aht * 0.35)))
            acw = int(handle * 0.18)
            talk = handle - acw
            disc = connected + dt.timedelta(seconds=talk)
            reason = r.choice(["AGENT_DISCONNECT", "CUSTOMER_DISCONNECT"])
            resolution = "RESOLVED" if r.random() < 0.82 else "ESCALATED"
        rows.append((
            f"{seq:08x}-6c1e-4a2b-9d3f-{seq * 7919 % 10**12:012d}", init, disc, channel, QUEUE_FOR[driver], "INBOUND",
            employee, driver, agent, enq, connected, talk, acw, reason, resolution,
        ))
        if not abandoned and allow_repeat:
            p = 0.07
            if driver == "password_reset":
                p = 0.30 if post else 0.08
            if r.random() < p:
                gap = dt.timedelta(hours=r.uniform(4, 6.5 * 24))
                nxt = start_local + gap
                if nxt.hour < 6 or nxt.hour >= 20:
                    nxt = nxt.replace(hour=r.randint(8, 16))
                if nxt < end_local:
                    emit(nxt, r.choice(["VOICE", "VOICE", "CHAT"]), employee, driver, allow_repeat=False)

    for i in range(DAYS):
        d = START + dt.timedelta(days=i)
        for channel in ("VOICE", "CHAT"):
            for _ in range(day_volume(d, channel)):
                m = arrival_minute(r, channel)
                local = dt.datetime.combine(d, dt.time(m // 60, m % 60, r.randint(0, 59)), tzinfo=ET)
                emp = f"E{r.randint(10000, 23999)}"
                emit(local, channel, emp, pick_driver(r, local >= OKTA_CHANGE), allow_repeat=True)

    cols = ["contact_id", "initiation_timestamp", "disconnect_timestamp", "channel", "queue_name", "initiation_method",
            "employee_id", "contact_driver", "agent_username", "enqueue_timestamp", "connected_to_agent_timestamp",
            "agent_interaction_duration_s", "after_contact_work_duration_s", "disconnect_reason", "resolution_code"]
    ts = pa.timestamp("us", tz="UTC")
    types = [pa.string(), ts, ts, pa.string(), pa.string(), pa.string(), pa.string(), pa.string(), pa.string(), ts, ts,
             pa.int32(), pa.int32(), pa.string(), pa.string()]
    rows.sort(key=lambda x: (x[1], x[0]))
    table = pa.table({c: pa.array([row[i] for row in rows], type=t) for i, (c, t) in enumerate(zip(cols, types))})
    pq.write_table(table, out / "contact_records.parquet")

    with open(out / "interval_staffing.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "interval_start", "staffed_agents"])
        for i in range(DAYS):
            d = START + dt.timedelta(days=i)
            for h in range(12, 40):
                hh, mm = divmod(h * 30, 60)
                base = 0 if d.weekday() >= 5 else 70
                shape = max(4, int(base * (1 - abs(10.5 - (hh + mm / 60)) / 9))) if base else 6
                if (d - START).days // 7 == 5:
                    shape = int(shape * 0.9)
                w.writerow([d.isoformat(), f"{hh:02d}:{mm:02d}", shape])
    with open(out / "change_log.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["change_id", "implemented_local", "summary", "service"])
        w.writerows(CHANGES)
    print(f"generate: {len(rows)} contact records -> {out}")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "data"))
