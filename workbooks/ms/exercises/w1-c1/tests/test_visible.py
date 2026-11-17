"""Visible tests: the happy path. Hidden tests cover reruns, late data, nulls and history."""

import polars as pl
from deltalake import DeltaTable

import medallion as m
from helpers import ev, land, paths, t


def test_dedupe_keeps_latest_event_then_ingest_seq():
    df = pl.DataFrame(
        [
            ev("S1", "PICKED", "UPS", "SEA", 1, 5, 1),
            ev("S1", "IN_TRANSIT", "UPS", "SEA", 3, 5, 2),
            ev("S1", "IN_TRANSIT_DUP", "UPS", "SEA", 3, 5, 3),
            ev("S2", "PICKED", "DHL", "PDX", 2, 5, 4),
        ],
        schema=m.BRONZE_SCHEMA,
    )
    out = m.dedupe_latest(df).sort("shipment_id")
    assert out["shipment_id"].to_list() == ["S1", "S2"]
    assert out["status"].to_list() == ["IN_TRANSIT_DUP", "PICKED"]


def test_first_batch_loads_silver_dim_and_watermark(tmp_path):
    p = paths(tmp_path)
    land(p["bronze_dir"], "b1", [
        ev("S1", "PICKED", "UPS", "SEA", 1, 10, 1),
        ev("S1", "IN_TRANSIT", "UPS", "SEA", 2, 10, 2),
        ev("S2", "PICKED", "DHL", "PDX", 3, 11, 3),
    ])
    res = m.run_batch(**p)
    silver = pl.read_delta(p["silver_path"]).sort("shipment_id")
    assert silver.height == 2
    assert silver.filter(pl.col("shipment_id") == "S1")["status"].item() == "IN_TRANSIT"
    dim = pl.read_delta(p["dim_path"])
    assert dim.height == 2 and dim["is_current"].all()
    assert m.read_watermark(p["control_path"], "shipments") == t(11)
    assert res.rows_read == 3 and res.rows_after_dedupe == 2


def test_second_batch_merges_and_opens_scd2_version(tmp_path):
    p = paths(tmp_path)
    land(p["bronze_dir"], "b1", [ev("S1", "PICKED", "UPS", "SEA", 1, 10, 1)])
    m.run_batch(**p)
    land(p["bronze_dir"], "b2", [ev("S1", "REROUTED", "UPS", "LAX", 200, 300, 2)])
    m.run_batch(**p)
    silver = pl.read_delta(p["silver_path"])
    assert silver.height == 1 and silver["status"].item() == "REROUTED"
    dim = pl.read_delta(p["dim_path"]).sort("version")
    assert dim["destination"].to_list() == ["SEA", "LAX"]
    assert dim["is_current"].to_list() == [False, True]
    assert dim["effective_to"][0] == t(200)
    assert DeltaTable(p["silver_path"]).version() == 1
