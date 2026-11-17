"""Visible checks: a day with no outage is exact (passes today); the outage day is exact (fails today)."""

import outage


def test_day_without_outage(tmp_path):
    r = outage.run_day(tmp_path / "a.db", outage=(0, 0), flaky=(0, 0))
    assert r["server"] == r["truth"]


def test_outage_day_counts_match_the_gateway(tmp_path):
    r = outage.run_day(tmp_path / "b.db")
    assert r["server"] == r["truth"], f"cloud {r['server']} vs gateway {r['truth']}"
