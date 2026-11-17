"""Visible tests for w2-c1 (happy path on fleet.json). The hidden suite covers the edge cases."""
import json
import subprocess
import sys
from pathlib import Path

import planner

ROOT = Path(__file__).resolve().parents[1]
FLEET = json.loads((ROOT / "fleet.json").read_text())


def by_cluster(result):
    return {c["cluster"]: c for w in result["waves"] for c in w["clusters"]}


def test_waves_follow_environment_order():
    res = planner.plan(FLEET)
    assert [w["environment"] for w in res["waves"]] == ["dev", "stg", "prod"]


def test_dev_cluster_steps_control_plane_first():
    c = by_cluster(planner.plan(FLEET))["dev-1"]
    assert [s["kind"] for s in c["steps"]] == ["control_plane", "node_pool"]
    assert c["steps"][0]["to"] == "1.34.1-gke.1200000"
    assert c["window_start"] == "2026-11-17T03:00:00Z"


def test_prod_blue_goes_one_minor_at_a_time():
    c = by_cluster(planner.plan(FLEET))["prod-blue"]
    cps = [s["to"] for s in c["steps"] if s["kind"] == "control_plane"]
    assert cps == ["1.33.5-gke.1080000", "1.34.1-gke.1200000"]


def test_cli_json():
    proc = subprocess.run([sys.executable, str(ROOT / "planner.py"), str(ROOT / "fleet.json"), "--json"],
                          capture_output=True, text=True, timeout=60)
    assert proc.returncode in (0, 1)
    assert "waves" in json.loads(proc.stdout)
