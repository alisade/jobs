"""Build fragmented Delta tables the way a streaming / micro-batch writer leaves them."""

import datetime as dt
import os

import polars as pl
from deltalake import DeltaTable

BASE = dt.datetime(2026, 10, 1, tzinfo=dt.timezone.utc)


def batch(start: int, n: int, region: str = "EU") -> pl.DataFrame:
    return pl.DataFrame(
        {
            "vehicle_id": [f"V{(start + i) % 37:03d}" for i in range(n)],
            "reading_ts": [BASE + dt.timedelta(seconds=start + i) for i in range(n)],
            "odometer_km": [float(10_000 + start + i) for i in range(n)],
            "region": [region] * n,
        }
    )


def fragmented(path: str, files: int, rows: int = 50, partitioned: bool = False, regions=("EU",),
               config: dict | None = None) -> str:
    """Append `files` tiny commits (one small file each, per region when partitioned)."""
    opts = {"partition_by": ["region"]} if partitioned else {}
    for i in range(files):
        for r in regions:
            df = batch(i * rows, rows, r)
            if i == 0 and r == regions[0] and config:
                df.write_delta(path, mode="append", delta_write_options={**opts, "configuration": config})
            else:
                df.write_delta(path, mode="append", delta_write_options=opts)
    return path


def big_files(path: str, files: int, rows: int = 20_000, region: str = "US", partitioned: bool = False) -> str:
    opts = {"partition_by": ["region"]} if partitioned else {}
    for i in range(files):
        batch(i * rows, rows, region).write_delta(path, mode="append", delta_write_options=opts)
    return path


def file_paths(path: str) -> set[str]:
    return set(DeltaTable(path).file_uris())


def physical_parquet(path: str) -> int:
    n = 0
    for d, _, fs in os.walk(path):
        if "_delta_log" in d:
            continue
        n += sum(1 for f in fs if f.endswith(".parquet"))
    return n
