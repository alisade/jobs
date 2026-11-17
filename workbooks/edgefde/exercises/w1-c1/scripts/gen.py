"""Deterministic test data for w1-c1: feature records, broker traffic and archived days.

    python scripts/gen.py <out_dir>     writes <out_dir>/2026-10-14 (good day) and 2026-10-15 (bad day)
"""

from __future__ import annotations

import json
import random
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

DEVICES = ["pump-01", "pump-02", "pump-03", "pump-04"]


def record(device: str, ts: datetime, seq: int, rng: random.Random, version: int = 1, **over) -> dict:
    r = {
        "schema_version": version,
        "device_id": device,
        "window_start": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window_s": 60,
        "seq": seq,
        "rms": round(rng.uniform(0.2, 1.5), 4),
        "peak": round(rng.uniform(1.0, 6.0), 4),
        "kurtosis": round(rng.uniform(2.6, 3.6), 4),
        "band_energy": [round(rng.uniform(0, 1), 4) for _ in range(4)],
    }
    if version == 2:
        r["temperature_c"] = round(rng.uniform(35, 60), 2)
    r.update(over)
    return r


def day_records(day: date, devices=DEVICES, seed: int = 7, drop: dict[str, float] | None = None) -> list[dict]:
    rng = random.Random(seed)
    start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    out = []
    for d_i, dev in enumerate(devices):
        for i in range(1440):
            if drop and rng.random() < drop.get(dev, 0.0):
                continue
            version = 2 if (dev == "pump-04" and i >= 720) else 1
            out.append(record(dev, start + timedelta(minutes=i), d_i * 100000 + i, rng, version))
    return out


INVALID_LINES = [
    b'{"device_id": "pump-02", "window_start": "2026-10-14T03:00:00", "window_s": 60, "seq": 1, "rms": 0.4, "peak": 1, "kurtosis": 3, "band_energy": [0,0,0,0]}',
    b'{"device_id": "pump-02", "window_start": "2026-10-14T03:01:00Z", "window_s": 60, "seq": 2, "rms": -1, "peak": 1, "kurtosis": 3, "band_energy": [0,0,0,0]}',
    b'{"device_id": "pump-02", "window_start": "2026-10-14T03:02:00Z", "window_s": 60, "seq": 3, "rms": 0.4, "peak": 1, "kurtosis": 3, "band_energy": [0,0,0]}',
    b'not json at all',
    b'{"device_id": "PUMP 9", "window_start": "2026-10-14T03:03:00Z", "window_s": 60, "seq": 4, "rms": 0.4, "peak": 1, "kurtosis": 3, "band_energy": [0,0,0,0]}',
]


def write_day(root: Path, day: date, records: list[dict], extra_lines: list[bytes] = (), dup_every: int = 0) -> Path:
    folder = root / day.isoformat()
    folder.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(r).encode() for r in records]
    if dup_every:
        lines += [lines[i] for i in range(0, len(lines), dup_every)]
    lines += list(extra_lines)
    half = len(lines) // 2
    (folder / "part-000.jsonl").write_bytes(b"\n".join(lines[:half]) + b"\n")
    (folder / "part-001.jsonl").write_bytes(b"\n".join(lines[half:]) + b"\n")
    return folder


def write_archive(root: Path) -> None:
    good = date(2026, 10, 14)
    write_day(root, good, day_records(good), INVALID_LINES, dup_every=97)
    bad = date(2026, 10, 15)
    write_day(root, bad, day_records(bad, seed=8, drop={"pump-03": 0.2}))


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "archive")
    write_archive(out)
    print(f"wrote archive days 2026-10-14 (good) and 2026-10-15 (pump-03 gappy) under {out}/")
