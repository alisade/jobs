"""Visible tests: the happy path through the review gate. Run: make test"""

from __future__ import annotations

import pytest

from durable.log import verify_log
from durable.run import ReviewError

EXC = ["CHG-104390", "CHG-104502"]


def test_run_pauses_for_review_then_finishes(world):
    run = world["start"]()
    out = run.run()
    assert out["awaiting_review"] == EXC
    assert len(out["done"]) == 4
    run.review("CHG-104390", reviewer="kbrooks", decision="confirm")
    run.review("CHG-104502", reviewer="kbrooks", decision="override",
               reason="Emergency change; CAB retro-approval minutes attached", evidence_ref="EV-CAB-2026-06-19.pdf p2")
    out = run.run()
    assert out["awaiting_review"] == [] and len(out["done"]) == 6
    assert [i.payload["sample_id"] for i in world["grc"].issues] == ["CHG-104390"]
    assert len(world["blob"].list_blobs(name_starts_with="CM03-2026Q3/workpaper/")) == 6
    assert verify_log(world["log"]) == []


def test_preparer_cannot_review(world):
    run = world["start"]()
    run.run()
    with pytest.raises(ReviewError):
        run.review("CHG-104390", reviewer="ralvarez", decision="confirm")
