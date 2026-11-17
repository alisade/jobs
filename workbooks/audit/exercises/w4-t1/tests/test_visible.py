"""Visible tests: the incident replay and two guards. Run: make test"""

from __future__ import annotations

from orchestrator.scenario import FAULTS

EXC = {"CHG-104390", "CHG-104502", "CHG-104611"}


def test_incident_replay_has_one_issue_per_exception(world, h):
    w = world(FAULTS)
    h.publish(w)
    issues = h.issues_by_sample(w["server"])
    assert set(issues) == EXC
    assert all(len(v) == 1 for v in issues.values()), f"duplicate GRC issues: {issues}"
    assert all(n == 1 for n in h.rows_by_sample(w["blob"]).values()), "duplicate workpaper rows"


def test_rate_limit_honors_retry_after(world, h):
    w = world({1: "429"})
    out = h.publish(w)
    assert 2.0 in w["sleeps"]
    assert set(out["issues"]) == EXC


def test_pass_samples_raise_no_issue(world, h):
    w = world()
    h.publish(w)
    assert set(h.issues_by_sample(w["server"])) == EXC
    assert len(w["blob"].rows()) == 6
