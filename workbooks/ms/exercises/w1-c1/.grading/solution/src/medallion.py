"""Northwind Logistics shipment events: bronze -> silver -> SCD2 dimension.

Local stand-in for a Fabric notebook. polars + deltalake (delta-rs) replace PySpark + Delta,
but the table semantics (MERGE, versions, time travel) are the same Delta protocol.
"""

from __future__ import annotations

import datetime as dt
import glob
import os
from dataclasses import dataclass

import polars as pl
from deltalake import DeltaTable, write_deltalake

TS = pl.Datetime("us", "UTC")

BRONZE_SCHEMA: dict[str, pl.DataType] = {
    "shipment_id": pl.String,
    "status": pl.String,
    "carrier": pl.String,
    "destination": pl.String,
    "weight_kg": pl.Float64,
    "event_ts": TS,
    "_ingested_at": TS,
    "_ingest_seq": pl.Int64,
}
SILVER_COLUMNS = list(BRONZE_SCHEMA)
DIM_TRACKED = ["carrier", "destination"]
DIM_SCHEMA: dict[str, pl.DataType] = {
    "shipment_id": pl.String,
    "carrier": pl.String,
    "destination": pl.String,
    "version": pl.Int64,
    "effective_from": TS,
    "effective_to": TS,
    "is_current": pl.Boolean,
}


class SchemaError(ValueError):
    """Raised when an incoming batch does not match the bronze contract."""


@dataclass
class BatchResult:
    rows_read: int
    rows_rejected: int
    rows_after_dedupe: int
    silver_inserted: int
    silver_updated: int
    dim_versions_added: int
    watermark: dt.datetime | None


def _exists(path: str) -> bool:
    return os.path.isdir(os.path.join(path, "_delta_log"))


# ---------------------------------------------------------------- watermark
def read_watermark(control_path: str, source: str) -> dt.datetime | None:
    if not _exists(control_path):
        return None
    df = pl.read_delta(control_path).filter(pl.col("source") == source)
    if df.is_empty():
        return None
    return df["watermark"].max()


def write_watermark(control_path: str, source: str, watermark: dt.datetime) -> None:
    current = read_watermark(control_path, source)
    if current is not None and watermark <= current:
        return  # never move backwards, and no empty commits
    row = pl.DataFrame(
        {
            "source": [source],
            "watermark": [watermark],
            "updated_at": [dt.datetime.now(dt.timezone.utc)],
        },
        schema={"source": pl.String, "watermark": TS, "updated_at": TS},
    )
    if not _exists(control_path):
        row.write_delta(control_path)
        return
    (
        row.write_delta(
            control_path,
            mode="merge",
            delta_merge_options={
                "predicate": "s.source = t.source",
                "source_alias": "s",
                "target_alias": "t",
            },
        )
        .when_matched_update_all()
        .when_not_matched_insert_all()
        .execute()
    )


# ---------------------------------------------------------------- bronze
def validate_schema(df: pl.DataFrame) -> None:
    missing = [c for c in BRONZE_SCHEMA if c not in df.columns]
    if missing:
        raise SchemaError(f"missing columns: {missing}")
    wrong = {
        c: str(df.schema[c]) for c, t in BRONZE_SCHEMA.items() if df.schema[c] != t
    }
    if wrong:
        raise SchemaError(f"wrong column types: {wrong}")


def read_bronze_increment(
    bronze_dir: str, watermark: dt.datetime | None, lookback: dt.timedelta
) -> pl.DataFrame:
    files = sorted(glob.glob(os.path.join(bronze_dir, "*.parquet")))
    if not files:
        return pl.DataFrame(schema=BRONZE_SCHEMA)
    frames = []
    for f in files:
        part = pl.read_parquet(f)
        validate_schema(part)
        frames.append(part.select(SILVER_COLUMNS))
    df = pl.concat(frames)
    if watermark is not None:
        df = df.filter(pl.col("_ingested_at") > watermark - lookback)
    return df


def reject_invalid(df: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    bad = pl.col("shipment_id").is_null() | pl.col("event_ts").is_null()
    return df.filter(~bad), df.filter(bad)


def dedupe_latest(df: pl.DataFrame, key: str = "shipment_id") -> pl.DataFrame:
    return (
        df.sort([key, "event_ts", "_ingest_seq"])
        .group_by(key, maintain_order=True)
        .last()
        .select(df.columns)
    )


# ---------------------------------------------------------------- silver
def merge_silver(df: pl.DataFrame, silver_path: str) -> tuple[int, int]:
    """Upsert latest-per-key rows. Returns (inserted, updated)."""
    validate_schema(df)
    if df.is_empty():
        return 0, 0
    df = df.select(SILVER_COLUMNS)
    if not _exists(silver_path):
        df.write_delta(silver_path)
        return df.height, 0
    metrics = (
        df.write_delta(
            silver_path,
            mode="merge",
            delta_merge_options={
                "predicate": "s.shipment_id = t.shipment_id",
                "source_alias": "s",
                "target_alias": "t",
            },
        )
        .when_matched_update_all(
            predicate=(
                "s.event_ts > t.event_ts OR "
                "(s.event_ts = t.event_ts AND s._ingest_seq > t._ingest_seq)"
            )
        )
        .when_not_matched_insert_all()
        .execute()
    )
    return int(metrics["num_target_rows_inserted"]), int(metrics["num_target_rows_updated"])


# ---------------------------------------------------------------- SCD2
def _same(a, b) -> bool:
    return a == b  # None == None is True: null-safe equality


def apply_scd2(changes: pl.DataFrame, dim_path: str) -> int:
    """Apply every change in event order. Returns versions added."""
    if changes.is_empty():
        return 0
    changes = changes.sort(["shipment_id", "event_ts", "_ingest_seq"])
    dim = pl.read_delta(dim_path) if _exists(dim_path) else pl.DataFrame(schema=DIM_SCHEMA)
    current = {
        r["shipment_id"]: r for r in dim.filter(pl.col("is_current")).iter_rows(named=True)
    }
    closes: dict[str, dt.datetime] = {}
    new_rows: list[dict] = []
    for key, grp in changes.group_by("shipment_id", maintain_order=True):
        key = key[0]
        prev = current.get(key)
        prev_vals = tuple(prev[c] for c in DIM_TRACKED) if prev else None
        prev_from = prev["effective_from"] if prev else None
        version = prev["version"] if prev else 0
        added: list[dict] = []
        for r in grp.iter_rows(named=True):
            if prev_from is not None and r["event_ts"] <= prev_from:
                continue  # replay or late row older than the open version
            vals = tuple(r[c] for c in DIM_TRACKED)
            if prev_vals is not None and all(_same(a, b) for a, b in zip(vals, prev_vals)):
                continue
            version += 1
            if added:
                added[-1]["effective_to"] = r["event_ts"]
                added[-1]["is_current"] = False
            elif prev is not None:
                closes[key] = r["event_ts"]
            added.append(
                {
                    "shipment_id": key,
                    "carrier": r["carrier"],
                    "destination": r["destination"],
                    "version": version,
                    "effective_from": r["event_ts"],
                    "effective_to": None,
                    "is_current": True,
                }
            )
            prev_vals, prev_from = vals, r["event_ts"]
        new_rows.extend(added)
    if not new_rows:
        return 0
    if closes:
        close_df = pl.DataFrame(
            {"shipment_id": list(closes), "closed_at": list(closes.values())},
            schema={"shipment_id": pl.String, "closed_at": TS},
        )
        dim = (
            dim.join(close_df, on="shipment_id", how="left")
            .with_columns(
                pl.when(pl.col("is_current") & pl.col("closed_at").is_not_null())
                .then(pl.col("closed_at"))
                .otherwise(pl.col("effective_to"))
                .alias("effective_to"),
                pl.when(pl.col("is_current") & pl.col("closed_at").is_not_null())
                .then(False)
                .otherwise(pl.col("is_current"))
                .alias("is_current"),
            )
            .drop("closed_at")
        )
    out = pl.concat([dim, pl.DataFrame(new_rows, schema=DIM_SCHEMA)]).sort(
        ["shipment_id", "version"]
    )
    out.write_delta(dim_path, mode="overwrite")
    return len(new_rows)


# ---------------------------------------------------------------- orchestration
def run_batch(
    bronze_dir: str,
    silver_path: str,
    dim_path: str,
    control_path: str,
    source: str = "shipments",
    lookback: dt.timedelta = dt.timedelta(hours=2),
) -> BatchResult:
    wm = read_watermark(control_path, source)
    raw = read_bronze_increment(bronze_dir, wm, lookback)
    good, bad = reject_invalid(raw)
    latest = dedupe_latest(good)
    ins, upd = merge_silver(latest, silver_path)
    versions = apply_scd2(good, dim_path)
    new_wm = wm
    if not raw.is_empty():
        batch_max = raw["_ingested_at"].max()
        new_wm = batch_max if wm is None else max(wm, batch_max)
        write_watermark(control_path, source, new_wm)
    return BatchResult(raw.height, bad.height, latest.height, ins, upd, versions, new_wm)
