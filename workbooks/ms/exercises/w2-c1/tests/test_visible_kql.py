"""Visible smoke checks. The hidden grader parses every clause much more strictly."""
import pathlib
import re

EX = pathlib.Path(__file__).resolve().parents[1]
Q = EX / "queries"


def code(name):
    text = (Q / name).read_text()
    return re.sub(r"//[^\n]*", "", text)


def test_all_query_files_present():
    names = sorted(p.name for p in Q.glob("*.kql"))
    assert names == ["01_speed_5min.kql", "02_latest_per_vehicle.kql", "03_update_policy.kql",
                     "04_materialized_view.kql", "05_trips.kql"]


def test_01_uses_5m_bin_and_no_take():
    c = code("01_speed_5min.kql")
    assert re.search(r"bin\(\s*Timestamp\s*,\s*5m\s*\)", c)
    assert not re.search(r"\|\s*(take|limit)\b", c)


def test_02_uses_arg_max():
    assert "arg_max(" in code("02_latest_per_vehicle.kql")


def test_03_has_function_and_policy():
    c = code("03_update_policy.kql")
    assert re.search(r"\.create-or-alter\s+function", c)
    assert re.search(r"\.alter\s+table\s+Telemetry\s+policy\s+update", c)


def test_04_creates_view():
    assert re.search(r"materialized-view", code("04_materialized_view.kql"))


def test_05_has_session_logic():
    c = code("05_trips.kql")
    assert any(x in c for x in ("row_window_session(", "prev(", "scan"))
