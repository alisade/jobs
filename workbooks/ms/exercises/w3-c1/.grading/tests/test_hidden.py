"""Hidden tests for ms/w3-c1."""

import json
import os

import polars as pl
import pytest
from deltalake import DeltaTable

import maintenance as mt
from helpers import big_files, file_paths, fragmented, physical_parquet

POLICY = dict(small_file_bytes=1_000_000, min_files=8, small_file_ratio=0.5)


def test_threshold_min_files_respected(tmp_path):
    p = fragmented(str(tmp_path / "t"), files=7)
    report = mt.run_maintenance({"t": p}, mt.Policy(**POLICY))
    assert report["tables"][0]["plan"]["action"] is None
    p2 = fragmented(str(tmp_path / "t2"), files=8)
    assert mt.run_maintenance({"t2": p2}, mt.Policy(**POLICY))["tables"][0]["plan"]["action"] == "compact"


def test_threshold_ratio_respected(tmp_path):
    p = big_files(str(tmp_path / "t"), files=6, rows=60_000)
    fragmented(p, files=4)  # 4 small out of 10 files = 0.4
    big = mt.table_health(p, small_file_bytes=200_000)
    assert big["small_files"] == 4 and big["small_file_ratio"] == 0.4
    plan = mt.plan_actions("t", big, mt.Policy(small_file_bytes=200_000, min_files=8, small_file_ratio=0.5))
    assert plan["action"] is None
    plan = mt.plan_actions("t", big, mt.Policy(small_file_bytes=200_000, min_files=8, small_file_ratio=0.4))
    assert plan["action"] == "compact"


def test_zorder_used_when_configured(tmp_path):
    p = fragmented(str(tmp_path / "t"), files=10)
    pol = mt.Policy(**POLICY, zorder={"t": ["vehicle_id"]})
    report = mt.run_maintenance({"t": p}, pol)
    assert report["tables"][0]["plan"]["action"] == "zorder"
    hist = [h["operation"] for h in DeltaTable(p).history()]
    assert "OPTIMIZE" in hist
    assert pl.read_delta(p).height == 500, "no rows lost"


def test_dry_run_changes_nothing(tmp_path):
    p = fragmented(str(tmp_path / "t"), files=10)
    v = DeltaTable(p).version()
    files = file_paths(p)
    phys = physical_parquet(p)
    report = mt.run_maintenance({"t": p}, mt.Policy(**POLICY), dry_run=True)
    t = report["tables"][0]
    assert report["dry_run"] is True
    assert t["plan"]["action"] == "compact", "dry run still reports the plan"
    assert t["optimize"] is None
    assert DeltaTable(p).version() == v
    assert file_paths(p) == files and physical_parquet(p) == phys


def test_retention_guard_blocks_short_retention(tmp_path):
    p = fragmented(str(tmp_path / "t"), files=2)
    with pytest.raises(mt.RetentionError):
        mt.vacuum_table(p, retention_hours=24, dry_run=True)


def test_retention_guard_honors_table_property(tmp_path):
    p = fragmented(str(tmp_path / "t"), files=2, config={"delta.deletedFileRetentionDuration": "interval 30 days"})
    with pytest.raises(mt.RetentionError):
        mt.vacuum_table(p, retention_hours=168, dry_run=True)
    assert mt.vacuum_table(p, retention_hours=720, dry_run=True) == []


def test_unsafe_override_vacuums_compacted_files(tmp_path):
    p = fragmented(str(tmp_path / "t"), files=10)
    mt.run_maintenance({"t": p}, mt.Policy(**POLICY))
    assert physical_parquet(p) == 11  # 10 tombstoned + 1 compacted
    planned = mt.vacuum_table(p, retention_hours=0, dry_run=True, allow_unsafe_retention=True)
    assert len(planned) == 10 and physical_parquet(p) == 11, "dry run must not delete"
    deleted = mt.vacuum_table(p, retention_hours=0, dry_run=False, allow_unsafe_retention=True)
    assert len(deleted) == 10 and physical_parquet(p) == 1
    assert pl.read_delta(p).height == 500


def test_default_job_does_not_delete_recent_tombstones(tmp_path):
    p = fragmented(str(tmp_path / "t"), files=10)
    report = mt.run_maintenance({"t": p}, mt.Policy(**POLICY))
    assert report["tables"][0]["vacuum"]["count"] == 0
    assert physical_parquet(p) == 11, "7-day retention keeps files removed today (time travel still works)"
    assert pl.read_delta(p, version=0).height == 50


def test_idempotent_second_run(tmp_path):
    p = fragmented(str(tmp_path / "t"), files=10)
    mt.run_maintenance({"t": p}, mt.Policy(**POLICY))
    v = DeltaTable(p).version()
    report = mt.run_maintenance({"t": p}, mt.Policy(**POLICY))
    assert report["tables"][0]["plan"]["action"] is None
    assert DeltaTable(p).version() == v


def test_partitioned_only_fragmented_partition_rewritten(tmp_path):
    p = str(tmp_path / "trips")
    fragmented(p, files=10, partitioned=True, regions=("EU",))
    fragmented(p, files=2, partitioned=True, regions=("US",))
    us_before = {f for f in file_paths(p) if "region=US" in f}
    h = mt.table_health(p, small_file_bytes=1_000_000)
    assert h["partition_columns"] == ["region"]
    by = {pp["values"]["region"]: pp for pp in h["partitions"]}
    assert by["EU"]["num_files"] == 10 and by["US"]["num_files"] == 2
    report = mt.run_maintenance({"trips": p}, mt.Policy(**POLICY))
    plan = report["tables"][0]["plan"]
    assert plan["action"] == "compact"
    assert len(plan["partition_filters"]) == 1
    after = file_paths(p)
    assert {f for f in after if "region=US" in f} == us_before, "healthy partition untouched"
    assert sum(1 for f in after if "region=EU" in f) == 1


def test_one_bad_table_does_not_stop_the_job(tmp_path):
    good = fragmented(str(tmp_path / "good"), files=10)
    report = mt.run_maintenance({"good": good, "missing": str(tmp_path / "nope")}, mt.Policy(**POLICY))
    assert report["status"] == "failed"
    assert [e["table"] for e in report["errors"]] == ["missing"]
    assert report["tables"][0]["table"] == "good" and report["tables"][0]["after"]["num_files"] == 1


def test_report_is_json_serializable_and_has_before_after(tmp_path):
    p = fragmented(str(tmp_path / "t"), files=10)
    report = mt.run_maintenance({"t": p}, mt.Policy(**POLICY))
    text = json.dumps(report)
    back = json.loads(text)
    t = back["tables"][0]
    for k in ("before", "after", "plan", "optimize", "vacuum"):
        assert k in t
    assert t["optimize"]["numFilesRemoved"] == 10 and t["optimize"]["numFilesAdded"] == 1


def test_cli_writes_report_and_exit_code(tmp_path):
    p = fragmented(str(tmp_path / "t"), files=10)
    cfg = tmp_path / "m.json"
    cfg.write_text(json.dumps({"tables": {"t": {"path": p}}, "policy": {**POLICY, "vacuum_retention_hours": 24}}))
    out = tmp_path / "r.json"
    rc = mt.main(["--config", str(cfg), "--report", str(out)])
    assert rc != 0, "a retention guard violation is a failed run"
    rep = json.loads(out.read_text())
    assert "RetentionError" in rep["errors"][0]["error"]
    cfg.write_text(json.dumps({"tables": {"t": {"path": p}}, "policy": POLICY}))
    assert mt.main(["--config", str(cfg), "--report", str(out), "--dry-run"]) == 0
    assert json.loads(out.read_text())["dry_run"] is True
