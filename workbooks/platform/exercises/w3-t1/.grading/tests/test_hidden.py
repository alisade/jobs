"""Hidden tests for platform/w3-t1."""
import json
from pathlib import Path

import pytest

import tfplan_sim

ROOT = Path.cwd()


def test_pure_import_and_no_creates():
    res = tfplan_sim.plan()
    assert all(c["action"] == "no-op" for c in res["changes"]), [c for c in res["changes"] if c["action"] != "no-op"]


def test_import_ids_unchanged():
    _, imports = tfplan_sim.load_config(ROOT / "migration")
    live = json.loads((ROOT / "live" / "inventory.json").read_text())
    assert set(imports.values()) == set(live)


@pytest.mark.parametrize("addr", ["google_compute_network.riq_legacy", "google_sql_database_instance.riq_legacy_pg"])
def test_prevent_destroy(addr):
    res, _ = tfplan_sim.load_config(ROOT / "migration")
    lc = (res[addr]["body"].get("lifecycle") or [{}])[0]
    assert lc.get("prevent_destroy") is True


def test_prevent_destroy_turns_a_future_replace_into_an_error(tmp_path):
    live = json.loads((ROOT / "live" / "inventory.json").read_text())
    live["projects/tsl-riq-prod/global/networks/riq-legacy"]["attrs"]["description"] = "edited by hand"
    p = tmp_path / "live.json"
    p.write_text(json.dumps(live))
    with pytest.raises(tfplan_sim.PlanError):
        tfplan_sim.plan(ROOT / "migration", p)


def test_network_attribute_explicit():
    res, _ = tfplan_sim.load_config(ROOT / "migration")
    assert res["google_compute_network.riq_legacy"]["body"].get("auto_create_subnetworks") is False
