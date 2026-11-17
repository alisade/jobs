"""Visible tests for w2-t1: run the drain simulator on your manifests."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import drain_sim  # noqa: E402


def test_every_node_drains():
    res = drain_sim.run(ROOT / "k8s", ROOT / "cluster" / "state.json")
    assert res["complete"], res["pending"]


def test_mdm_budgets_untouched():
    st = {s["name"]: s for s in drain_sim.run(ROOT / "k8s", ROOT / "cluster" / "state.json")["pdbs_before"]}
    assert st["mdm/mdm-api"]["disruptionsAllowed"] == 1
    assert st["mdm/rdm-cache"]["disruptionsAllowed"] == 1
