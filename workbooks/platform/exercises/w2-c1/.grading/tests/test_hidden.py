"""Hidden tests for platform/w2-c1."""
import copy
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

import planner

ROOT = Path.cwd()
BASE = json.loads((ROOT / "fleet.json").read_text())
T = "1.34.1-gke.1200000"


def fleet(*names, **over):
    f = copy.deepcopy(BASE)
    if names:
        f["clusters"] = [c for c in f["clusters"] if c["name"] in names]
    for k, v in over.items():
        f[k] = v
    return f


def cl(f, name):
    return next(c for c in f["clusters"] if c["name"] == name)


def by_cluster(res):
    return {c["cluster"]: c for w in res["waves"] for c in w["clusters"]}


def blocked(res):
    return {b["cluster"]: " ".join(b["reasons"]) for b in res["blocked"]}


def t(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def test_fixture_schedule_and_quota_block():
    res = planner.plan(fleet())
    got = {k: v["window_start"] for k, v in by_cluster(res).items()}
    assert got == {"dev-1": "2026-11-17T03:00:00Z", "stg-1": "2026-11-19T03:00:00Z", "prod-blue": "2026-12-03T03:00:00Z"}
    assert "quota" in blocked(res)["prod-green"].lower()


def test_skew_forces_pool_upgrade_before_last_hop():
    steps = by_cluster(planner.plan(fleet("prod-blue")))["prod-blue"]["steps"]
    seq = [(s["kind"], s.get("pool"), s["to"]) for s in steps]
    i_cp2 = seq.index(("control_plane", None, T))
    i_pool = seq.index(("node_pool", "legacy-io", "1.33.5-gke.1080000"))
    assert i_pool < i_cp2
    assert seq[-2:] == [("node_pool", "default", T), ("node_pool", "legacy-io", T)] or \
        sorted(seq[-2:]) == sorted([("node_pool", "default", T), ("node_pool", "legacy-io", T)])
    # pools never newer than the control plane at any point
    cp = "1.32.9-gke.1100000"
    for kind, _, to in seq:
        if kind == "control_plane":
            cp = to
        else:
            assert planner.parse_version(to) <= planner.parse_version(cp)


def test_pdb_zero_blocks_and_holds_later_clusters():
    f = fleet()
    cl(f, "stg-1")["pdbs"][0]["disruptions_allowed"] = 0
    res = planner.plan(f)
    assert "riq/riq-api" in blocked(res)["stg-1"]
    assert set(res["held"]) == {"prod-blue", "prod-green"}
    assert list(by_cluster(res)) == ["dev-1"]


def test_target_not_in_channel_blocks():
    f = fleet("prod-blue")
    f["channel_versions"]["STABLE"].remove(T)
    assert "channel" in blocked(planner.plan(f))["prod-blue"].lower()


def test_missing_intermediate_minor_blocks():
    f = fleet("prod-blue")
    f["channel_versions"]["STABLE"] = [v for v in f["channel_versions"]["STABLE"] if not v.startswith("1.33.")]
    assert "prod-blue" in blocked(planner.plan(f))


def test_cluster_already_at_target_is_skipped():
    f = fleet("dev-1")
    c = cl(f, "dev-1")
    c["control_plane"] = T
    c["node_pools"][0]["version"] = T
    res = planner.plan(f)
    assert res["waves"] == [] and res["blocked"] == []


def test_exclusion_scopes():
    # patch-only rollout: 1.34.1 -> 1.34.2 on REGULAR
    def run(scope):
        f = fleet("dev-1", target_version="1.34.2-gke.1050000")
        c = cl(f, "dev-1")
        c["control_plane"] = T
        c["node_pools"][0]["version"] = T
        c["exclusions"] = [{"name": "x", "start": "2026-11-16T00:00:00Z", "end": "2026-11-20T00:00:00Z", "scope": scope}]
        return by_cluster(planner.plan(f))["dev-1"]["window_start"]
    assert run("NO_MINOR_UPGRADES") == "2026-11-17T03:00:00Z"          # patches allowed
    assert run("NO_MINOR_OR_NODE_UPGRADES") == "2026-11-24T03:00:00Z"  # node patch blocked
    assert run("NO_UPGRADES") == "2026-11-24T03:00:00Z"


def test_minor_blocked_by_no_minor_upgrades():
    f = fleet("dev-1")
    cl(f, "dev-1")["exclusions"] = [{"name": "x", "start": "2026-11-16T00:00:00Z", "end": "2026-11-20T00:00:00Z",
                                     "scope": "NO_MINOR_UPGRADES"}]
    assert by_cluster(planner.plan(f))["dev-1"]["window_start"] == "2026-11-24T03:00:00Z"


def test_no_window_within_horizon_blocks():
    f = fleet("dev-1")
    cl(f, "dev-1")["exclusions"] = [{"name": "freeze", "start": "2026-11-01T00:00:00Z", "end": "2027-03-01T00:00:00Z",
                                     "scope": "NO_UPGRADES"}]
    assert "window" in blocked(planner.plan(f))["dev-1"].lower()


def test_quota_surge_vs_blue_green():
    f = fleet("prod-green")
    c = cl(f, "prod-green")
    c["node_pools"][0]["strategy"] = {"type": "SURGE", "max_surge": 2, "max_unavailable": 0}
    c["quota"]["cpus_used"] = 124  # 36 free; surge needs max(2*8, 1*16) = 16
    assert "prod-green" in by_cluster(planner.plan(f))
    c["quota"]["cpus_used"] = 150  # 10 free
    assert "prod-green" in blocked(planner.plan(f))


def test_canary_first_and_gaps_and_soak():
    f = fleet()
    cl(f, "prod-green")["quota"]["cpus_used"] = 50
    res = planner.plan(f)
    prod = [c["cluster"] for c in res["waves"][2]["clusters"]]
    assert prod == ["prod-blue", "prod-green"]
    w = by_cluster(res)
    assert t(w["stg-1"]["window_start"]) - t(w["dev-1"]["window_start"]) >= dt.timedelta(hours=48)
    assert t(w["prod-blue"]["window_start"]) - t(w["stg-1"]["window_start"]) >= dt.timedelta(hours=72)
    assert t(w["prod-green"]["window_start"]) - t(w["prod-blue"]["window_start"]) >= dt.timedelta(hours=24)
    assert w["prod-green"]["window_start"] == "2026-12-08T03:00:00Z"


def test_cli_exit_codes(tmp_path):
    p = subprocess.run([sys.executable, str(ROOT / "planner.py"), str(ROOT / "fleet.json")], capture_output=True, text=True, timeout=60)
    assert p.returncode == 1  # prod-green is blocked
    bad = tmp_path / "f.json"
    bad.write_text("[]")
    p = subprocess.run([sys.executable, str(ROOT / "planner.py"), str(bad)], capture_output=True, text=True, timeout=60)
    assert p.returncode == 2
