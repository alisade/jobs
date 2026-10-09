"""Visible tests: health report and a basic compaction run."""

import maintenance as mt
from helpers import file_paths, fragmented

POLICY = dict(small_file_bytes=1_000_000, min_files=8, small_file_ratio=0.5)


def test_health_counts_small_files(tmp_path):
    p = fragmented(str(tmp_path / "telemetry"), files=10)
    h = mt.table_health(p, small_file_bytes=1_000_000)
    assert h["num_files"] == 10
    assert h["small_files"] == 10
    assert h["small_file_ratio"] == 1.0
    assert h["version"] == 9
    assert 0 < h["min_file_bytes"] <= h["avg_file_bytes"] <= h["max_file_bytes"]


def test_fragmented_table_is_compacted(tmp_path):
    p = fragmented(str(tmp_path / "telemetry"), files=10)
    report = mt.run_maintenance({"telemetry": p}, mt.Policy(**POLICY))
    t = report["tables"][0]
    assert t["plan"]["action"] == "compact"
    assert t["after"]["num_files"] == 1
    assert report["status"] == "succeeded"


def test_healthy_table_is_left_alone(tmp_path):
    p = fragmented(str(tmp_path / "small"), files=3)
    before = file_paths(p)
    report = mt.run_maintenance({"small": p}, mt.Policy(**POLICY))
    assert report["tables"][0]["plan"]["action"] is None
    assert file_paths(p) == before
