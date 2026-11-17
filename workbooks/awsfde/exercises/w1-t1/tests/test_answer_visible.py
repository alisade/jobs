"""Visible checks for w1-t1. The grader runs more (including the replay thresholds)."""

from __future__ import annotations

import json

from w1t1_support import StubBedrock

from answer_svc import service


def test_answer_happy_path():
    b = StubBedrock()
    b.ok("SH-10001 is in transit.")
    with b.stub:
        r = service.answer("Where is SH-10001?", b.client, sleep=lambda s: None)
    assert r["statusCode"] == 200
    assert json.loads(r["body"])["answer"] == "SH-10001 is in transit."


def test_invalid_request_is_400_and_not_retried():
    b = StubBedrock()
    b.error("ValidationException", 400)
    with b.stub:
        r = service.answer("x" * 10, b.client, sleep=lambda s: None)
    assert r["statusCode"] == 400
    assert b.calls == 1


def test_replay_runs():
    from replay.sim import load_release, run
    from w1t1_support import ROOT
    res = run(load_release(ROOT, "visible_answer_svc"), "2026-11-09")
    s = res["summary"]
    assert s["requests"] > 7000 and "error_rate" in s
