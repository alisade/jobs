"""Hidden tests for edgefde/w5-c1: gates, phases, concurrency, offline handling, resume."""

import json
import sys
from collections import Counter
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fleet.rollout import Policy, RolloutController, RolloutInProgress  # noqa: E402
from fleet.sim import Fleet  # noqa: E402


def go(tmp_path, version, fleet=None, policy=Policy(), max_windows=500):
    f = fleet or Fleet()
    c = RolloutController(f, tmp_path / "state.json", policy)
    c.start("v6", version)
    return f, c, c.run(max_windows=max_windows)


def calls_to(f, version):
    return [(w, d) for w, d, v in f.desired_calls if v == version]


def test_canary_first_and_soaks(tmp_path):
    f, _, r = go(tmp_path, "v7")
    calls = calls_to(f, "v7")
    assert calls[0][1] == "gw-01"
    assert calls[1][0] - calls[0][0] >= 3, "the next device was updated before the canary soaked"
    assert r.status == "succeeded" and sorted(r.updated) == f.ids()
    assert r.rolled_back == [] and r.skipped_offline == []


@pytest.mark.parametrize("version,word", [("v7-crash", "down"), ("v7-storm", "alert"), ("v7-slow", "latency")])
def test_bad_models_stop_at_canary(tmp_path, version, word):
    f, _, r = go(tmp_path, version)
    assert r.status == "rolled_back" and r.failed_phase == 0
    assert r.rolled_back == ["gw-01"]
    assert len({d for _, d in calls_to(f, version)}) == 1, "only the canary may get a failing model"
    assert word in (r.reason or "").lower()
    assert set(f.versions().values()) == {"v6"}


def test_failure_in_later_phase_rolls_back_everything_touched(tmp_path):
    f, _, r = go(tmp_path, "v7-rev2bad")
    assert r.status == "rolled_back"
    assert r.failed_phase == 3  # rev2 boards gw-07..gw-10 first appear in the 100% phase
    touched = {d for _, d in calls_to(f, "v7-rev2bad")}
    assert set(r.rolled_back) == touched and len(touched) > 5
    assert set(f.versions().values()) == {"v6"}


def test_max_concurrent_respected(tmp_path):
    f, _, r = go(tmp_path, "v7", policy=Policy(max_concurrent=2))
    per_window = Counter(w for w, _ in calls_to(f, "v7"))
    assert max(per_window.values()) <= 2
    assert r.status == "succeeded"


def test_short_offline_waits_and_completes(tmp_path):
    f = Fleet()
    f.take_offline("gw-03", 8)
    f, _, r = go(tmp_path, "v7", fleet=f)
    assert r.status == "succeeded" and r.skipped_offline == []
    assert f.versions()["gw-03"] == "v7"


def test_long_offline_is_skipped_not_failed(tmp_path):
    f = Fleet()
    f.take_offline("gw-05", 200)
    f, _, r = go(tmp_path, "v7", fleet=f)
    assert r.status == "succeeded"
    assert r.skipped_offline == ["gw-05"]
    assert f.devices["gw-05"].desired == "v6", "a skipped device must come back on the known-good model"


def test_offline_canary_candidate_is_passed_over(tmp_path):
    f = Fleet()
    f.take_offline("gw-01", 50)
    f, _, r = go(tmp_path, "v7-crash", fleet=f)
    assert calls_to(f, "v7-crash")[0][1] == "gw-02"
    assert r.status == "rolled_back"


def test_resume_after_controller_crash(tmp_path):
    f, c, r = go(tmp_path, "v7", max_windows=5)
    assert r.status == "in_progress"
    del c
    c2 = RolloutController(f, tmp_path / "state.json")
    r2 = c2.run()
    assert r2.status == "succeeded" and set(f.versions().values()) == {"v7"}
    per_dev = Counter(d for _, d in calls_to(f, "v7"))
    assert max(per_dev.values()) == 1, "resume must not restart the rollout from scratch"


def test_resume_mid_failure_path_still_rolls_back(tmp_path):
    f, c, r = go(tmp_path, "v7-rev2bad", max_windows=8)
    assert r.status == "in_progress"
    r2 = RolloutController(f, tmp_path / "state.json").run()
    assert r2.status == "rolled_back" and set(f.versions().values()) == {"v6"}


def test_no_two_rollouts_at_once(tmp_path):
    f, c, r = go(tmp_path, "v7", max_windows=3)
    with pytest.raises(RolloutInProgress):
        RolloutController(f, tmp_path / "state.json").start("v6", "v7-storm")
    RolloutController(f, tmp_path / "state.json").run()
    c3 = RolloutController(f, tmp_path / "state.json")
    c3.start("v7", "v6")  # finished rollouts do not block the next one
    assert c3.run().status == "succeeded"


def test_state_file_is_json_with_status(tmp_path):
    go(tmp_path, "v7")
    assert json.loads((tmp_path / "state.json").read_text())["status"] == "succeeded"
