"""Hidden tests for audit/w4-t1: commit-then-timeout and crashes at several points."""

from __future__ import annotations

import pytest

from orchestrator.fakes import ProcessCrash

EXC = {"CHG-104390", "CHG-104502", "CHG-104611"}


def assert_exactly_once(h, w):
    issues = h.issues_by_sample(w["server"])
    assert set(issues) == EXC, issues
    assert all(len(v) == 1 for v in issues.values()), f"duplicate GRC issues: {issues}"
    rows = h.rows_by_sample(w["blob"])
    assert len(rows) == 6 and all(n == 1 for n in rows.values()), f"workpaper rows: {rows}"


SCHEDULES = {
    "first-commit-timeout": {1: "commit_timeout"},
    "second-sample-commit-timeout": {2: "commit_timeout"},
    "two-commit-timeouts-step-retry": {1: "commit_timeout", 2: "commit_timeout"},
    "commit-timeout-then-lost": {3: "commit_timeout", 4: "timeout"},
    "mixed-with-429": {1: "timeout", 2: "commit_timeout", 3: "429", 5: "commit_timeout"},
    "lost-requests-only": {1: "timeout", 2: "timeout"},
}


@pytest.mark.parametrize("faults", list(SCHEDULES.values()), ids=list(SCHEDULES))
def test_faults_never_duplicate_side_effects(world, h, faults):
    w = world(faults)
    out = h.publish(w)
    assert sorted(out["published"]) == sorted(s["sample_id"] for s in w["samples"]) and not out["failed"]
    assert_exactly_once(h, w)
    assert set(out["issues"]) == EXC


@pytest.mark.parametrize("req", [1, 2, 3])
def test_crash_after_commit_then_restart(world, h, tmp_path, req):
    w = world({req: "commit_crash"})
    with pytest.raises(ProcessCrash):
        h.publish(w)
    # new process: same GRC, same blob, same checkpoint db, no faults left
    w2 = world(server=w["server"], blob=w["blob"], db=tmp_path / "cp.db")
    w2["server"].faults.clear()
    out = h.publish(w2)
    assert not out["failed"]
    assert_exactly_once(h, w2)


def _record_keys(server):
    keys = []
    orig = server.handle

    def handle(method, path, headers, body):
        keys.append((body.get("run_id"), body.get("sample_id"), headers.get("Idempotency-Key")))
        return orig(method, path, headers, body)
    server.handle = handle
    return keys


def test_same_key_on_every_attempt_distinct_per_sample(world, h):
    w = world({1: "commit_timeout", 2: "timeout", 4: "429"})
    keys = _record_keys(w["server"])
    h.publish(w)
    per = {}
    for _, sid, k in keys:
        per.setdefault(sid, set()).add(k)
    assert all(len(v) == 1 for v in per.values()), per
    assert len({next(iter(v)) for v in per.values()}) == len(per)


def test_new_run_gets_new_issues(world, h, tmp_path):
    w = world()
    h.publish(w)
    w2 = world(run_id="CM03-2026Q4", server=w["server"], blob=w["blob"], db=tmp_path / "cp.db")
    h.publish(w2)
    assert len(w["server"].issues) == 6
    assert {i["run_id"] for i in w["server"].issues} == {"CM03-2026Q3", "CM03-2026Q4"}


def test_rerun_of_finished_run_is_a_no_op(world, h, tmp_path):
    w = world()
    h.publish(w)
    n, appends = w["server"].n, w["blob"].appends
    w2 = world(server=w["server"], blob=w["blob"], db=tmp_path / "cp.db")
    out = h.publish(w2)
    assert w["server"].n == n and w["blob"].appends == appends
    assert len(out["published"]) == 6
