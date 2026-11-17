"""Backfill one archived day into the feature store. Safe to run any number of times.

    python -m ingest.backfill --db features.db --archive archive --day 2026-10-14 \
        --devices pump-01,pump-02,pump-03,pump-04
Exit code 0 on success, 2 when data quality fails (nothing written), 1 on bad usage.

TODO: implement backfill() and main() (README "Backfill").
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

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
    raise NotImplementedError("TODO")


def main(argv: list[str] | None = None) -> int:
    raise NotImplementedError("TODO")


if __name__ == "__main__":
    sys.exit(main())
