"""Hidden tests for ms/w1-c1: reruns, late data, same-batch changes, nulls, history, schema."""

import datetime as dt

import polars as pl
import pytest
from deltalake import DeltaTable

import medallion as m
from helpers import SCHEMA, ev, land, paths, t


def _run(p, **kw):
    return m.run_batch(**p, **kw)


def test_rerun_same_files_is_idempotent(tmp_path):
    p = paths(tmp_path)
    land(p["bronze_dir"], "b1", [
        ev("S1", "PICKED", "UPS", "SEA", 1, 10, 1),
        ev("S2", "PICKED", "DHL", "PDX", 2, 10, 2),
    ])
    _run(p)
    silver_v = DeltaTable(p["silver_path"]).version()
    dim_v = DeltaTable(p["dim_path"]).version()
    res = _run(p)  # within lookback: same rows are re-read
    assert pl.read_delta(p["silver_path"]).height == 2
    assert pl.read_delta(p["dim_path"]).height == 2
    assert res.dim_versions_added == 0
    assert DeltaTable(p["dim_path"]).version() == dim_v, "no commit when nothing changed"
    assert res.silver_inserted == 0 and res.silver_updated == 0
    # silver may be re-merged with a no-op, but must not gain rows
    assert DeltaTable(p["silver_path"]).version() >= silver_v


def test_empty_increment_makes_no_commits(tmp_path):
    p = paths(tmp_path)
    land(p["bronze_dir"], "b1", [ev("S1", "PICKED", "UPS", "SEA", 1, 10, 1)])
    _run(p, lookback=dt.timedelta(0))
    v = (DeltaTable(p["silver_path"]).version(), DeltaTable(p["dim_path"]).version(),
         DeltaTable(p["control_path"]).version())
    res = _run(p, lookback=dt.timedelta(0))
    assert res.rows_read == 0
    assert (DeltaTable(p["silver_path"]).version(), DeltaTable(p["dim_path"]).version(),
            DeltaTable(p["control_path"]).version()) == v


def test_watermark_filters_old_files_outside_lookback(tmp_path):
    p = paths(tmp_path)
    land(p["bronze_dir"], "b1", [ev("S1", "PICKED", "UPS", "SEA", 1, 10, 1)])
    _run(p, lookback=dt.timedelta(minutes=30))
    land(p["bronze_dir"], "b2", [ev("S2", "PICKED", "DHL", "PDX", 500, 600, 2)])
    _run(p, lookback=dt.timedelta(minutes=30))
    land(p["bronze_dir"], "b3", [ev("S3", "PICKED", "DHL", "PDX", 800, 900, 3)])
    res = _run(p, lookback=dt.timedelta(minutes=30))
    # b1 (ingested t+10) is far outside watermark(600) - 30 min; b2 is re-read by the lookback
    assert res.rows_read == 2
    assert m.read_watermark(p["control_path"], "shipments") == t(900)


def test_lookback_catches_late_landed_file(tmp_path):
    p = paths(tmp_path)
    land(p["bronze_dir"], "b1", [ev("S1", "PICKED", "UPS", "SEA", 1, 100, 1)])
    _run(p, lookback=dt.timedelta(minutes=30))
    # a file stamped before the watermark lands after the run (clock skew / slow copy)
    land(p["bronze_dir"], "b0_late", [ev("S9", "PICKED", "FDX", "BOS", 2, 90, 9)])
    res = _run(p, lookback=dt.timedelta(minutes=30))
    assert "S9" in pl.read_delta(p["silver_path"])["shipment_id"].to_list()
    assert m.read_watermark(p["control_path"], "shipments") == t(100), "watermark never moves back"
    assert res.rows_read == 2


def test_late_older_event_does_not_overwrite_newer_silver(tmp_path):
    p = paths(tmp_path)
    land(p["bronze_dir"], "b1", [ev("S1", "DELIVERED", "UPS", "SEA", 300, 310, 5)])
    _run(p)
    land(p["bronze_dir"], "b2", [ev("S1", "PICKED", "UPS", "SEA", 10, 320, 6)])
    _run(p)
    silver = pl.read_delta(p["silver_path"])
    assert silver["status"].item() == "DELIVERED"
    assert silver["event_ts"].item() == t(300)


def test_same_batch_multiple_changes_create_ordered_versions(tmp_path):
    p = paths(tmp_path)
    land(p["bronze_dir"], "b1", [
        ev("S1", "REROUTED", "UPS", "DEN", 30, 40, 3),  # out of file order on purpose
        ev("S1", "PICKED", "UPS", "SEA", 10, 40, 1),
        ev("S1", "IN_TRANSIT", "UPS", "SEA", 20, 40, 2),  # untracked change only
        ev("S1", "HANDOFF", "FDX", "DEN", 50, 40, 4),
    ])
    _run(p)
    dim = pl.read_delta(p["dim_path"]).sort("version")
    assert dim["version"].to_list() == [1, 2, 3]
    assert list(zip(dim["carrier"], dim["destination"])) == [("UPS", "SEA"), ("UPS", "DEN"), ("FDX", "DEN")]
    assert dim["effective_from"].to_list() == [t(10), t(30), t(50)]
    assert dim["effective_to"].to_list()[:2] == [t(30), t(50)]
    assert dim["effective_to"][2] is None
    assert dim["is_current"].to_list() == [False, False, True]
    assert dim.filter(pl.col("is_current")).height == 1


def test_untracked_change_does_not_version(tmp_path):
    p = paths(tmp_path)
    land(p["bronze_dir"], "b1", [ev("S1", "PICKED", "UPS", "SEA", 1, 10, 1)])
    _run(p)
    land(p["bronze_dir"], "b2", [ev("S1", "IN_TRANSIT", "UPS", "SEA", 200, 300, 2, weight=11.0)])
    res = _run(p)
    assert res.dim_versions_added == 0
    assert pl.read_delta(p["dim_path"]).height == 1


def test_null_tracked_attribute_is_null_safe(tmp_path):
    p = paths(tmp_path)
    land(p["bronze_dir"], "b1", [ev("S1", "PICKED", None, "SEA", 1, 10, 1)])
    _run(p)
    land(p["bronze_dir"], "b2", [ev("S1", "PICKED2", None, "SEA", 200, 300, 2)])
    assert _run(p).dim_versions_added == 0, "null == null must not open a version"
    land(p["bronze_dir"], "b3", [ev("S1", "ASSIGNED", "UPS", "SEA", 400, 500, 3)])
    assert _run(p).dim_versions_added == 1


def test_rows_with_null_key_or_event_ts_are_rejected(tmp_path):
    p = paths(tmp_path)
    land(p["bronze_dir"], "b1", [
        ev(None, "PICKED", "UPS", "SEA", 1, 10, 1),
        ev("S2", "PICKED", "UPS", "SEA", None, 10, 2),
        ev("S3", "PICKED", "UPS", "SEA", 3, 10, 3),
    ])
    res = _run(p)
    assert res.rows_rejected == 2
    assert pl.read_delta(p["silver_path"])["shipment_id"].to_list() == ["S3"]
    assert pl.read_delta(p["dim_path"]).height == 1


def test_history_and_time_travel(tmp_path):
    p = paths(tmp_path)
    land(p["bronze_dir"], "b1", [ev("S1", "PICKED", "UPS", "SEA", 1, 10, 1)])
    _run(p)
    land(p["bronze_dir"], "b2", [ev("S1", "DELIVERED", "UPS", "SEA", 200, 300, 2)])
    _run(p, lookback=dt.timedelta(0))
    dt_ = DeltaTable(p["silver_path"])
    assert dt_.version() == 1
    ops = [h["operation"] for h in dt_.history()]
    assert "MERGE" in ops
    v0 = pl.read_delta(p["silver_path"], version=0)
    assert v0["status"].item() == "PICKED"


def test_schema_drift_is_rejected_before_any_write(tmp_path):
    p = paths(tmp_path)
    land(p["bronze_dir"], "b1", [ev("S1", "PICKED", "UPS", "SEA", 1, 10, 1)])
    _run(p)
    bad_schema = dict(SCHEMA)
    bad_schema["weight_kg"] = pl.String  # producer started sending "12.5kg"
    row = ev("S2", "PICKED", "UPS", "SEA", 200, 300, 2)
    row["weight_kg"] = "12.5kg"
    pl.DataFrame([row], schema=bad_schema).write_parquet(p["bronze_dir"] + "/b2.parquet")
    with pytest.raises(m.SchemaError):
        _run(p)
    assert pl.read_delta(p["silver_path"]).height == 1
    assert m.read_watermark(p["control_path"], "shipments") == t(10), "watermark must not advance on failure"


def test_merge_silver_rejects_missing_column(tmp_path):
    p = paths(tmp_path)
    df = pl.DataFrame([ev("S1", "PICKED", "UPS", "SEA", 1, 10, 1)], schema=SCHEMA).drop("_ingest_seq")
    with pytest.raises(m.SchemaError):
        m.merge_silver(df, p["silver_path"])


def test_tie_on_event_ts_uses_ingest_seq_across_batches(tmp_path):
    p = paths(tmp_path)
    land(p["bronze_dir"], "b1", [ev("S1", "A", "UPS", "SEA", 100, 110, 1)])
    _run(p)
    land(p["bronze_dir"], "b2", [ev("S1", "B", "UPS", "SEA", 100, 400, 2)])
    _run(p)
    assert pl.read_delta(p["silver_path"])["status"].item() == "B"
