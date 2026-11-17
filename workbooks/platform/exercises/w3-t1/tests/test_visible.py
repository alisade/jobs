"""Visible tests for w3-t1."""
import tfplan_sim


def test_batch_is_a_pure_import():
    s = tfplan_sim.plan()["summary"]
    assert (s["add"], s["change"], s["destroy"]) == (0, 0, 0), s
    assert s["import"] == 5
