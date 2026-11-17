"""Contoso Fleet lakehouse table maintenance job.

Local stand-in for a scheduled Fabric notebook / Lakehouse Maintenance activity: health report,
OPTIMIZE (bin-compaction or Z-order), VACUUM with a retention guard, JSON report.
delta-rs does the Delta work; it does NOT write V-Order (a Fabric-only write optimization).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from dataclasses import asdict, dataclass, field

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
def _stats(sizes: list[int], small_file_bytes: int) -> dict:
    n = len(sizes)
    small = sum(1 for s in sizes if s < small_file_bytes)
    return {
        "num_files": n,
        "total_bytes": int(sum(sizes)),
        "avg_file_bytes": int(sum(sizes) / n) if n else 0,
        "min_file_bytes": int(min(sizes)) if n else 0,
        "max_file_bytes": int(max(sizes)) if n else 0,
        "small_files": small,
        "small_file_ratio": round(small / n, 4) if n else 0.0,
    }


def table_health(path: str, small_file_bytes: int) -> dict:
    t = DeltaTable(path)
    actions = _add_actions(t)
    part_cols = list(t.metadata().partition_columns)
    health = {
        "path": path,
        "version": t.version(),
        "partition_columns": part_cols,
        **_stats(actions["size_bytes"].to_list() if actions.height else [], small_file_bytes),
        "partitions": [],
    }
    if part_cols and actions.height:
        keys = [f"partition.{c}" for c in part_cols]
        for grp_key, grp in actions.group_by(keys, maintain_order=True):
            values = dict(zip(part_cols, [None if v is None else str(v) for v in grp_key]))
            health["partitions"].append(
                {"values": values, **_stats(grp["size_bytes"].to_list(), small_file_bytes)}
            )
        health["partitions"].sort(key=lambda p: json.dumps(p["values"], sort_keys=True))
    return health


# ---------------------------------------------------------------- planning
def _breaches(stats: dict, policy: Policy) -> bool:
    return stats["num_files"] >= policy.min_files and stats["small_file_ratio"] >= policy.small_file_ratio


def plan_actions(name: str, health: dict, policy: Policy) -> dict:
    """Decide OPTIMIZE for one table. Returns {"action": None|"compact"|"zorder", "partition_filters": [...], "reason": str}."""
    zcols = policy.zorder.get(name) or []
    if health["partition_columns"]:
        hot = [p for p in health["partitions"] if _breaches(p, policy)]
        if not hot:
            return {"action": None, "partition_filters": [], "reason": "no partition breaches thresholds"}
        filters = [[(c, "=", v) for c, v in p["values"].items()] for p in hot]
        reason = f"{len(hot)} partition(s) with >= {policy.min_files} files and small-file ratio >= {policy.small_file_ratio}"
        return {"action": "zorder" if zcols else "compact", "partition_filters": filters, "reason": reason}
    if not _breaches(health, policy):
        return {"action": None, "partition_filters": [], "reason": "below thresholds"}
    reason = (
        f"{health['small_files']}/{health['num_files']} files under {policy.small_file_bytes} bytes"
    )
    return {"action": "zorder" if zcols else "compact", "partition_filters": [], "reason": reason}


# ---------------------------------------------------------------- vacuum
_INTERVAL = re.compile(r"interval\s+(\d+)\s+(hour|hours|day|days|week|weeks)", re.I)


def table_min_retention_hours(table: DeltaTable) -> int:
    """Max of the 7-day default and the table's delta.deletedFileRetentionDuration."""
    conf = table.metadata().configuration or {}
    raw = conf.get("delta.deletedFileRetentionDuration")
    hours = MIN_RETENTION_HOURS
    if raw:
        m = _INTERVAL.search(raw)
        if m:
            n, unit = int(m.group(1)), m.group(2).lower()
            mult = 1 if unit.startswith("hour") else 24 if unit.startswith("day") else 168
            hours = max(hours, n * mult)
    return hours


def vacuum_table(path: str, retention_hours: int, dry_run: bool = True, allow_unsafe_retention: bool = False) -> list[str]:
    t = DeltaTable(path)
    minimum = table_min_retention_hours(t)
    if retention_hours < minimum and not allow_unsafe_retention:
        raise RetentionError(
            f"retention {retention_hours}h is below the minimum {minimum}h for {path}; "
            "pass allow_unsafe_retention=True only if no reader or writer needs older versions"
        )
    files = t.vacuum(
        retention_hours=retention_hours,
        dry_run=dry_run,
        enforce_retention_duration=not allow_unsafe_retention,
    )
    return sorted(files)


# ---------------------------------------------------------------- job
def maintain_table(name: str, path: str, policy: Policy, dry_run: bool) -> dict:
    minimum = table_min_retention_hours(DeltaTable(path))
    if policy.vacuum_retention_hours < minimum and not policy.allow_unsafe_retention:
        # fail before touching anything, not after the OPTIMIZE
        raise RetentionError(f"retention {policy.vacuum_retention_hours}h is below the minimum {minimum}h for {path}")
    before = table_health(path, policy.small_file_bytes)
    plan = plan_actions(name, before, policy)
    entry: dict = {"table": name, "before": before, "plan": plan, "optimize": None, "vacuum": None, "after": None}
    if plan["action"] and not dry_run:
        t = DeltaTable(path)
        filters = plan["partition_filters"] or [None]
        totals = {"numFilesAdded": 0, "numFilesRemoved": 0}
        for f in filters:
            kwargs = {"partition_filters": f} if f else {}
            if policy.target_file_bytes:
                kwargs["target_size"] = policy.target_file_bytes
            if plan["action"] == "zorder":
                m = t.optimize.z_order(policy.zorder[name], **kwargs)
            else:
                m = t.optimize.compact(**kwargs)
            totals["numFilesAdded"] += int(m["numFilesAdded"])
            totals["numFilesRemoved"] += int(m["numFilesRemoved"])
            t = DeltaTable(path)
        entry["optimize"] = totals
    files = vacuum_table(path, policy.vacuum_retention_hours, dry_run=dry_run,
                         allow_unsafe_retention=policy.allow_unsafe_retention)
    entry["vacuum"] = {"dry_run": dry_run, "retention_hours": policy.vacuum_retention_hours,
                       "files": files, "count": len(files)}
    entry["after"] = table_health(path, policy.small_file_bytes)
    return entry


def run_maintenance(tables: dict[str, str], policy: Policy, dry_run: bool = False) -> dict:
    report = {
        "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "dry_run": dry_run,
        "policy": asdict(policy),
        "tables": [],
        "errors": [],
    }
    for name in sorted(tables):
        try:
            report["tables"].append(maintain_table(name, tables[name], policy, dry_run))
        except Exception as e:  # one broken table must not stop the others
            report["errors"].append({"table": name, "error": f"{type(e).__name__}: {e}"})
    report["status"] = "failed" if report["errors"] else "succeeded"
    return report


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
