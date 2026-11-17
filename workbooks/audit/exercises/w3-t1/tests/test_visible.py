"""Visible test: two nightly runs in separate processes. make test"""

from conftest import counts, night


def test_second_night_does_not_retest(tmp_path):
    night(tmp_path)
    night(tmp_path)
    c = counts(tmp_path)
    assert all(n == 1 for n in c["tested"].values()), c["tested"]
