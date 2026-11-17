"""Visible tests: the happy path end to end."""

def test_fp32_matches_sklearn(built):
    assert built["report"]["parity_max_abs_diff"] < 1e-4


def test_int8_within_budget(built):
    r = built["report"]
    assert r["within_budget"], r["violations"]
    assert r["int8"]["size_bytes"] < r["fp32"]["size_bytes"]


def test_report_files_written(built):
    assert (built["out"] / "report.json").exists() and (built["out"] / "report.md").exists()
