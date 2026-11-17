"""Hidden tests for audit/w4-c1: crash/resume, idempotent side effects, review gate, log chain."""

from __future__ import annotations

import json

import pytest

from durable.fakes import CrashInjected
from durable.log import verify_log
from durable.run import ReviewError, idempotency_key

EXC = ["CHG-104390", "CHG-104502"]
RID = "CM03-2026Q3"


def drive(world, crash=None, decisions=None):
    """Run to completion, restarting the 'process' after every injected crash."""
    decisions = decisions or {s: ("confirm", None, None) for s in EXC}
    run = world["start"](crash)
    restarts = 0
    for _ in range(12):
        try:
            out = run.run()
            if out["awaiting_review"]:
                for sid in out["awaiting_review"]:
                    d, r, e = decisions[sid]
                    run.review(sid, reviewer="kbrooks", decision=d, reason=r, evidence_ref=e)
                continue
            return run, out, restarts
        except CrashInjected:
            restarts += 1
            run = world["start"]()
    raise AssertionError("run did not finish")


def lines(world):
    return [json.loads(x) for x in world["log"].read_text().splitlines() if x.strip()]


def test_idempotency_key():
    assert idempotency_key("R1", "CHG-1", "grc_issue") == "R1/CHG-1/grc_issue"


CRASHES = [
    ("CHG-104118", "evidence", "after"), ("CHG-104118", "test", "after"),
    ("CHG-104163", "workpaper", "before"), ("CHG-104163", "workpaper", "after"),
    ("CHG-104390", "workpaper", "after"), ("CHG-104390", "grc_issue", "before"),
    ("CHG-104390", "grc_issue", "after"), ("CHG-104502", "grc_issue", "after"),
]


@pytest.mark.parametrize("crash", CRASHES, ids=["-".join(c) for c in CRASHES])
def test_resume_after_crash_has_no_duplicate_side_effects(world, crash):
    run, out, restarts = drive(world, crash)
    assert restarts == 1, "the injected crash did not fire: call _crash() at every step"
    assert len(out["done"]) == 6
    grc = world["grc"]
    assert sorted(i.payload["sample_id"] for i in grc.issues) == EXC
    for sid in EXC:
        keys = {r["key"] for r in grc.requests if r["payload"]["sample_id"] == sid}
        assert keys == {idempotency_key(RID, sid, "grc_issue")}
    names = world["blob"].writes
    assert len(names) == len(set(names)) == 6
    for (step, sid), n in world["calls"].items():
        expect = 2 if (sid, step, "after") == crash and step in ("evidence", "test") else 1
        assert n == expect, f"{step} for {sid} ran {n} times"
    assert verify_log(world["log"]) == []


def test_committed_steps_never_rerun_after_review(world):
    drive(world)
    assert all(n == 1 for n in world["calls"].values())
    assert len(world["calls"]) == 12


def test_review_survives_restart(world):
    run = world["start"]()
    run.run()
    run.review("CHG-104390", reviewer="kbrooks", decision="confirm")
    run2 = world["start"]()
    assert run2.pending_reviews() == ["CHG-104502"]
    out = run2.run()
    assert "CHG-104390" in out["done"] and out["awaiting_review"] == ["CHG-104502"]
    assert [i.payload["sample_id"] for i in world["grc"].issues] == ["CHG-104390"]


def test_override_publishes_pass_without_issue(world):
    reason = "Emergency change; CAB retro-approval minutes attached"
    drive(world, decisions={"CHG-104390": ("confirm", None, None),
                            "CHG-104502": ("override", reason, "EV-CAB-2026-06-19.pdf p2")})
    assert [i.payload["sample_id"] for i in world["grc"].issues] == ["CHG-104390"]
    row = json.loads(world["blob"].download_blob(f"{RID}/workpaper/CHG-104502.json").readall())
    assert row["conclusion"] == "pass" and row["model_conclusion"] == "exception"
    assert row["review"]["reviewer"] == "kbrooks" and row["review"]["reason"] == reason
    assert row["review"]["evidence_ref"] == "EV-CAB-2026-06-19.pdf p2"
    assert row["preparer"] == "ralvarez" and row["control"] == "CM-03"
    passed = json.loads(world["blob"].download_blob(f"{RID}/workpaper/CHG-104118.json").readall())
    assert passed["conclusion"] == "pass" and passed["review"] is None


@pytest.mark.parametrize("kw", [
    {"reviewer": " RAlvarez ", "decision": "confirm"},
    {"reviewer": "kbrooks", "decision": "override", "reason": "", "evidence_ref": "EV-1"},
    {"reviewer": "kbrooks", "decision": "override", "reason": "CAB minutes", "evidence_ref": None},
    {"reviewer": "kbrooks", "decision": "approve"},
], ids=["preparer-case", "no-reason", "no-evidence-ref", "bad-decision"])
def test_review_rules(world, kw):
    run = world["start"]()
    run.run()
    with pytest.raises(ReviewError):
        run.review("CHG-104390", **kw)
    assert run.status("CHG-104390") == "awaiting_review"


def test_cannot_review_twice_or_review_a_pass(world):
    run = world["start"]()
    run.run()
    with pytest.raises(ReviewError):
        run.review("CHG-104118", reviewer="kbrooks", decision="confirm")
    run.review("CHG-104390", reviewer="kbrooks", decision="confirm")
    with pytest.raises(ReviewError):
        run.review("CHG-104390", reviewer="mlee", decision="override", reason="x", evidence_ref="y")


def test_conflicting_existing_workpaper_is_not_overwritten(world):
    world["blob"].upload_blob(f"{RID}/workpaper/CHG-104118.json", '{"tampered": true}')
    run = world["start"]()
    with pytest.raises(Exception):
        run.run()
    assert world["blob"].download_blob(f"{RID}/workpaper/CHG-104118.json").readall() == b'{"tampered": true}'


def test_log_records_steps_and_reviews(world):
    drive(world)
    recs = lines(world)
    done = [(r["data"]["sample_id"], r["data"]["step"]) for r in recs if r["kind"] == "step_completed"]
    assert len(done) == len(set(done))
    assert ("CHG-104390", "test") in done and ("CHG-104390", "grc_issue") in done
    reviews = [r for r in recs if r["kind"] == "review"]
    assert {r["data"]["sample_id"] for r in reviews} == set(EXC)
    assert all(r["data"]["reviewer"] == "kbrooks" and r["data"]["decision"] == "confirm" for r in reviews)


def test_log_chain_continues_across_restart(world):
    drive(world, ("CHG-104163", "workpaper", "after"))
    recs = lines(world)
    assert [r["seq"] for r in recs] == list(range(len(recs)))
    assert sum(1 for r in recs if r["kind"] == "run_started") == 1
    assert sum(1 for r in recs if r["kind"] == "run_resumed") >= 1
    for a, b in zip(recs, recs[1:]):
        assert b["prev"] == a["hash"]


def _rewrite(world, recs):
    world["log"].write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in recs))


def test_verify_detects_edit(world):
    drive(world)
    recs = lines(world)
    i = next(n for n, r in enumerate(recs) if r["kind"] == "review")
    recs[i]["data"]["decision"] = "override"
    _rewrite(world, recs)
    assert verify_log(world["log"])


def test_verify_detects_deletion(world):
    drive(world)
    recs = lines(world)
    del recs[3]
    _rewrite(world, recs)
    assert verify_log(world["log"])


def test_verify_detects_reorder(world):
    drive(world)
    recs = lines(world)
    recs[2], recs[3] = recs[3], recs[2]
    _rewrite(world, recs)
    assert verify_log(world["log"])


def test_verify_detects_recomputed_hash_without_chain(world):
    import hashlib
    drive(world)
    recs = lines(world)
    r = recs[4]
    r["data"]["note"] = "inserted"
    body = json.dumps({"seq": r["seq"], "kind": r["kind"], "data": r["data"], "prev": r["prev"]}, sort_keys=True, separators=(",", ":"))
    r["hash"] = hashlib.sha256(body.encode()).hexdigest()
    _rewrite(world, recs)
    problems = verify_log(world["log"])
    assert problems and any("5" in p or "6" in p for p in problems)
