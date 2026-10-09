"""Test helpers: write bronze parquet files the way the landing pipeline does."""

import datetime as dt
import os

import polars as pl

TS = pl.Datetime("us", "UTC")
UTC = dt.timezone.utc
BASE = dt.datetime(2026, 10, 12, 1, 0, tzinfo=UTC)

SCHEMA = {
    "shipment_id": pl.String,
    "status": pl.String,
    "carrier": pl.String,
    "destination": pl.String,
    "weight_kg": pl.Float64,
    "event_ts": TS,
    "_ingested_at": TS,
    "_ingest_seq": pl.Int64,
}


def t(minutes: float) -> dt.datetime:
    return BASE + dt.timedelta(minutes=minutes)


def ev(sid, status, carrier, dest, event_min, ingest_min, seq, weight=10.0):
    return {
        "shipment_id": sid,
        "status": status,
        "carrier": carrier,
        "destination": dest,
        "weight_kg": weight,
        "event_ts": None if event_min is None else t(event_min),
        "_ingested_at": t(ingest_min),
        "_ingest_seq": seq,
    }


def land(bronze_dir: str, name: str, rows: list[dict]) -> str:
    os.makedirs(bronze_dir, exist_ok=True)
    path = os.path.join(bronze_dir, f"{name}.parquet")
    pl.DataFrame(rows, schema=SCHEMA).write_parquet(path)
    return path


def paths(tmp_path):
    return {
        "bronze_dir": str(tmp_path / "Files" / "bronze" / "shipments"),
        "silver_path": str(tmp_path / "Tables" / "silver_shipments"),
        "dim_path": str(tmp_path / "Tables" / "dim_shipment"),
        "control_path": str(tmp_path / "Tables" / "etl_control"),
    }
