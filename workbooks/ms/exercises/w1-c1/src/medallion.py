"""Northwind Logistics shipment events: bronze -> silver -> SCD2 dimension.

Local stand-in for a Fabric notebook. polars + deltalake (delta-rs) replace PySpark + Delta,
but the table semantics (MERGE, versions, time travel) are the same Delta protocol.

Fill in every function marked TODO. Keep the signatures: the tests call them directly.
See README.md for the contract of each step.
"""

from __future__ import annotations

import datetime as dt
import glob  # noqa: F401  (you will likely need it)
import os
from dataclasses import dataclass

import polars as pl
from deltalake import DeltaTable, write_deltalake  # noqa: F401

TS = pl.Datetime("us", "UTC")

# The bronze contract: landing files must have exactly these columns and types.
BRONZE_SCHEMA: dict[str, pl.DataType] = {
    "shipment_id": pl.String,
    "status": pl.String,
    "carrier": pl.String,
    "destination": pl.String,
    "weight_kg": pl.Float64,
    "event_ts": TS,
    "_ingested_at": TS,  # set by the landing pipeline when the file was copied in
    "_ingest_seq": pl.Int64,  # monotonically increasing per landing pipeline run
}
SILVER_COLUMNS = list(BRONZE_SCHEMA)

# SCD2 dimension: one row per version of a shipment's routing.
DIM_TRACKED = ["carrier", "destination"]
DIM_SCHEMA: dict[str, pl.DataType] = {
    "shipment_id": pl.String,
    "carrier": pl.String,
    "destination": pl.String,
    "version": pl.Int64,  # 1, 2, 3 ... per shipment_id
    "effective_from": TS,  # event_ts of the change
    "effective_to": TS,  # null while current
    "is_current": pl.Boolean,
}


class SchemaError(ValueError):
    """Raised when an incoming batch does not match the bronze contract."""


@dataclass
class BatchResult:
    rows_read: int  # rows returned by read_bronze_increment (before rejects)
    rows_rejected: int  # rows with null shipment_id or null event_ts
    rows_after_dedupe: int  # rows passed to merge_silver
    silver_inserted: int
    silver_updated: int
    dim_versions_added: int
    watermark: dt.datetime | None  # watermark after the run


def _exists(path: str) -> bool:
    """True when a Delta table exists at path."""
    return os.path.isdir(os.path.join(path, "_delta_log"))


# ---------------------------------------------------------------- watermark
def read_watermark(control_path: str, source: str) -> dt.datetime | None:
    """Return the stored watermark for `source` from the control Delta table, or None."""
    # TODO
    raise NotImplementedError


def write_watermark(control_path: str, source: str, watermark: dt.datetime) -> None:
    """Upsert (source, watermark, updated_at) into the control Delta table.

    Never move a watermark backwards, and do not commit when the value would not change.
    """
    # TODO
    raise NotImplementedError


# ---------------------------------------------------------------- bronze
def validate_schema(df: pl.DataFrame) -> None:
    """Raise SchemaError if any BRONZE_SCHEMA column is missing or has a different dtype."""
    # TODO
    raise NotImplementedError


def read_bronze_increment(
    bronze_dir: str, watermark: dt.datetime | None, lookback: dt.timedelta
) -> pl.DataFrame:
    """Read every *.parquet file in bronze_dir, validate each, and return the increment.

    Increment = rows with _ingested_at > watermark - lookback (all rows when watermark is None).
    Return an empty frame with BRONZE_SCHEMA when there are no files.
    """
    # TODO
    raise NotImplementedError


def reject_invalid(df: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Split into (good, rejected): rejected rows have a null shipment_id or null event_ts."""
    # TODO
    raise NotImplementedError


def dedupe_latest(df: pl.DataFrame, key: str = "shipment_id") -> pl.DataFrame:
    """One row per key: the latest event_ts, ties broken by the highest _ingest_seq."""
    # TODO
    raise NotImplementedError


# ---------------------------------------------------------------- silver
def merge_silver(df: pl.DataFrame, silver_path: str) -> tuple[int, int]:
    """MERGE latest-per-key rows into the silver Delta table. Returns (inserted, updated).

    - Create the table on first write.
    - Insert new keys; update existing keys ONLY when the incoming row is newer
      (event_ts greater, or equal event_ts and greater _ingest_seq).
    - Validate the schema first; write nothing for an empty frame.
    """
    # TODO
    raise NotImplementedError


# ---------------------------------------------------------------- SCD2
def apply_scd2(changes: pl.DataFrame, dim_path: str) -> int:
    """Apply every (non-deduplicated) change to the SCD2 dimension in event order.

    Returns the number of versions added. See README for the rules (null-safe compare,
    same-batch multiple changes, replays, no commit when nothing changed).
    """
    # TODO
    raise NotImplementedError


# ---------------------------------------------------------------- orchestration
def run_batch(
    bronze_dir: str,
    silver_path: str,
    dim_path: str,
    control_path: str,
    source: str = "shipments",
    lookback: dt.timedelta = dt.timedelta(hours=2),
) -> BatchResult:
    """One notebook run: read increment -> reject -> dedupe -> merge silver -> SCD2 -> watermark.

    Commit the watermark last, and only when the increment was not empty, so a failure
    anywhere earlier leaves it untouched and the next run re-reads the same rows.
    """
    # TODO
    raise NotImplementedError
