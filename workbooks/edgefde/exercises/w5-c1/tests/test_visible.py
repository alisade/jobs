"""Visible tests: a good model reaches the whole fleet; a crashing model stops at the canary."""

from fleet.rollout import RolloutController
from fleet.sim import Fleet


def test_good_model_reaches_everyone(tmp_path):
    f = Fleet()
    c = RolloutController(f, tmp_path / "state.json")
    c.start("v6", "v7")
    r = c.run()
    assert r.status == "succeeded"
    assert set(f.versions().values()) == {"v7"}


def test_crashing_model_rolls_back_at_canary(tmp_path):
    f = Fleet()
    c = RolloutController(f, tmp_path / "state.json")
    c.start("v6", "v7-crash")
    r = c.run()
    assert r.status == "rolled_back" and r.failed_phase == 0
    assert set(f.versions().values()) == {"v6"}
