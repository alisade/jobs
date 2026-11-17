"""Visible tests: the agent still reviews normal samples. Run: make test"""

from __future__ import annotations

import json

from conftest import recorded
from reviewagent.agent import review
from reviewagent.scripted import scripted


def test_normal_sample_reviews(store, evidence_dir):
    res = review(scripted(recorded("CHG-104118")), "CHG-104118", store, evidence_dir)
    assert json.loads(res.final_text)["recommendation"] == "no_change"
    assert res.trace == []


def test_self_approved_change_stays_open(store, evidence_dir):
    review(scripted(recorded("CHG-104240")), "CHG-104240", store, evidence_dir)
    assert store.exception("EXC-2026-0415")["status"] == "open"


def test_overnight_replay_does_not_close_exc_0412(store, evidence_dir):
    review(scripted(recorded("CHG-104233")), "CHG-104233", store, evidence_dir)
    assert store.exception("EXC-2026-0412")["status"] == "open"
