"""Contoso Fleet lakehouse table maintenance job.

Local stand-in for a scheduled Fabric notebook / Lakehouse Maintenance activity: health report,
OPTIMIZE (bin-compaction or Z-order), VACUUM with a retention guard, JSON report.
delta-rs does the Delta work; it does NOT write V-Order (a Fabric-only write optimization).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re  # noqa: F401
import sys
from dataclasses import asdict, dataclass, field  # noqa: F401

import polars as pl
import pyarrow as pa
from deltalake import DeltaTable

MIN_RETENTION_HOURS = 168  # 7 days: Delta / Fabric default safety check


class RetentionError(ValueError):
    """VACUUM retention below the allowed minimum without an explicit override."""


@dataclass
class Policy:
    small_file_bytes: int = 32 * 1024 * 1024  # files below this count as "small"
    min_files: int = 8  # do not bother below this many files (per table or partition)
    small_file_ratio: float = 0.5  # compact when this share of files is small
    target_file_bytes: int | None = None  # passed to delta-rs as target_size
    vacuum_retention_hours: int = MIN_RETENTION_HOURS
    allow_unsafe_retention: bool = False
    zorder: dict[str, list[str]] = field(default_factory=dict)  # table name -> z-order columns


def _add_actions(table: DeltaTable) -> pl.DataFrame:
    """Active data files of the current version as a polars frame (path, size_bytes, partition.*)."""
    return pl.DataFrame(pa.table(table.get_add_actions(flatten=True)))


# ---------------------------------------------------------------- health
def table_health(path: str, small_file_bytes: int) -> dict:
    """Health of the current table version. Return a dict with at least:

    path, version, partition_columns, num_files, total_bytes, avg_file_bytes, min_file_bytes,
    max_file_bytes, small_files (size < small_file_bytes), small_file_ratio (rounded to 4 places),
    and partitions: for a partitioned table one entry per partition, sorted, shaped
    {"values": {col: str_value}, num_files, total_bytes, ..., small_file_ratio}; [] otherwise.
    Hint: _add_actions() gives path, size_bytes and partition.<col> per active file.
    """
    # TODO
    raise NotImplementedError


# ---------------------------------------------------------------- planning
def plan_actions(name: str, health: dict, policy: Policy) -> dict:
    """Decide OPTIMIZE for one table.

    Return {"action": None | "compact" | "zorder", "partition_filters": [...], "reason": str}.
    A table (or, when partitioned, a partition) breaches when num_files >= policy.min_files AND
    small_file_ratio >= policy.small_file_ratio. Partitioned tables: only breaching partitions are
    rewritten; partition_filters is a list with one delta-rs filter per partition, e.g.
    [[("region", "=", "EU")]]. Use "zorder" when policy.zorder has columns for this table.
    """
    # TODO
    raise NotImplementedError


# ---------------------------------------------------------------- vacuum
def table_min_retention_hours(table: DeltaTable) -> int:
    """Max of MIN_RETENTION_HOURS and the table property delta.deletedFileRetentionDuration
    (values look like "interval 30 days" or "interval 240 hours")."""
    # TODO
    raise NotImplementedError


def vacuum_table(path: str, retention_hours: int, dry_run: bool = True, allow_unsafe_retention: bool = False) -> list[str]:
    """VACUUM with a retention guard.

    Raise RetentionError when retention_hours is below table_min_retention_hours() unless
    allow_unsafe_retention is True. Return the sorted list of files deleted (dry run: that would be).
    """
    # TODO
    raise NotImplementedError


# ---------------------------------------------------------------- job
def maintain_table(name: str, path: str, policy: Policy, dry_run: bool) -> dict:
    """One table. Check the retention guard BEFORE touching anything, then
    health -> plan -> optimize (skipped in dry run) -> vacuum -> health after.

    Return {"table", "before", "plan", "optimize": None | {"numFilesAdded", "numFilesRemoved"},
            "vacuum": {"dry_run", "retention_hours", "files", "count"}, "after"}.
    """
    # TODO
    raise NotImplementedError


def run_maintenance(tables: dict[str, str], policy: Policy, dry_run: bool = False) -> dict:
    """Run every table (sorted by name). One failing table must not stop the others.

    Return {"started_at", "dry_run", "policy", "tables": [maintain_table results],
            "errors": [{"table", "error": "<ExceptionType>: <message>"}],
            "status": "succeeded" | "failed"}. Must be JSON serializable.
    """
    # TODO
    raise NotImplementedError


def load_config(path: str) -> tuple[dict[str, str], Policy]:
    with open(path) as f:
        cfg = json.load(f)
    tables = {n: t["path"] for n, t in cfg["tables"].items()}
    zorder = {n: t["zorder"] for n, t in cfg["tables"].items() if t.get("zorder")}
    keys = {"small_file_bytes", "min_files", "small_file_ratio", "target_file_bytes",
            "vacuum_retention_hours", "allow_unsafe_retention"}
    policy = Policy(**{k: v for k, v in cfg.get("policy", {}).items() if k in keys}, zorder=zorder)
    return tables, policy


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Lakehouse table maintenance")
    ap.add_argument("--config", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    tables, policy = load_config(args.config)
    report = run_maintenance(tables, policy, dry_run=args.dry_run)
    with open(args.report, "w") as f:
        json.dump(report, f, indent=2, default=str)
    for t in report["tables"]:
        print(f"{t['table']}: plan={t['plan']['action']} files {t['before']['num_files']} -> {t['after']['num_files']} "
              f"vacuum={t['vacuum']['count']}")
    for e in report["errors"]:
        print(f"ERROR {e['table']}: {e['error']}")
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
