"""Backfill one archived day into the feature store. Safe to run any number of times.

    python -m ingest.backfill --db features.db --archive archive --day 2026-10-14 \
        --devices pump-01,pump-02,pump-03,pump-04
Exit code 0 on success, 2 when data quality fails (nothing written), 1 on bad usage.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .dq import DataQualityError, check_day
from .models import InvalidRecord, parse_record
from .store import FeatureStore


@dataclass
class BackfillResult:
    day: str
    read: int
    valid: int
    quarantined: int
    written: int
    rows_for_day: int


def backfill(store: FeatureStore, archive: str | Path, day: date, expected_devices: list[str],
             window_s: int = 60) -> BackfillResult:
    folder = Path(archive) / day.isoformat()
    files = sorted(folder.glob("*.jsonl"))
    if not files:
        raise FileNotFoundError(f"no archive files in {folder}")
    good, bad, read = [], [], 0
    for f in files:
        with f.open("rb") as fh:
            for n, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                read += 1
                try:
                    good.append(parse_record(line))
                except InvalidRecord as exc:
                    bad.append((line, str(exc), f"{f.name}:{n}"))
    issues = check_day(good, day, expected_devices, window_s=window_s)
    if issues:
        raise DataQualityError(issues)
    written = store.write_batch(good, bad)
    return BackfillResult(day.isoformat(), read, len(good), len(bad), written, store.count_for_day(day.isoformat()))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="ingest.backfill")
    ap.add_argument("--db", required=True)
    ap.add_argument("--archive", required=True)
    ap.add_argument("--day", required=True, type=date.fromisoformat)
    ap.add_argument("--devices", required=True)
    args = ap.parse_args(argv)
    store = FeatureStore(args.db)
    try:
        res = backfill(store, args.archive, args.day, [d for d in args.devices.split(",") if d])
    except DataQualityError as exc:
        print(f"DATA QUALITY FAILED, nothing written: {exc}", file=sys.stderr)
        return 2
    finally:
        store.close()
    print(f"backfill {res.day}: read={res.read} valid={res.valid} quarantined={res.quarantined} "
          f"written={res.written} rows_for_day={res.rows_for_day}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
