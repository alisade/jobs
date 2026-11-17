"""Visible tests for w4-t1."""
import xpsim


def test_every_team_database_ready():
    res = xpsim.run()
    bad = [x["xr"] + ": " + x["message"] for x in res["xrs"] if not x["Ready"]]
    assert not bad, bad
