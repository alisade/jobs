"""Visible tests: replay the incident window through the current loop."""

from __future__ import annotations

from ait1_support import recorded_turns

from agentloop.replay import replay_all, replay_turn


async def test_plain_search_turn_returns_the_recorded_answer():
    record = next(r for r in recorded_turns() if r["turn_id"] == "turn-0002")
    outcome = await replay_turn(record)
    assert outcome.error is None, outcome.error
    assert outcome.text == record["final_text"]


async def test_replaying_the_incident_window_produces_no_400s():
    report = await replay_all(recorded_turns())
    failed = [(o.record["turn_id"], str(o.error)[:160]) for o in report.bad_requests]
    assert failed == [], f"{len(failed)} turns still fail with HTTP 400: {failed[:2]}"
