"""Visible checks: the day without restarts (passes today) and the real day with restarts (fails today)."""

from __future__ import annotations

import simulate


def test_day_without_restarts_is_complete(tmp_path):
    res = simulate.run_scenario(tmp_path / "a.db", restarts={})
    assert res["distinct"] == 8640 and res["rows"] == 8640


def test_day_with_supervisor_restarts_is_complete(tmp_path):
    res = simulate.run_scenario(tmp_path / "b.db")
    assert res["distinct"] == 8640, f"{8640 - res['distinct']} windows missing from the dashboard"
    assert res["rows"] == 8640, f"{res['rows'] - res['distinct']} duplicate rows"
