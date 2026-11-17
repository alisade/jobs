"""Hidden checks for connect/w2-c3: results equal the reference queries on a freshly generated dataset."""

from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "scripts"))
from db import connect, run_file  # noqa: E402


@pytest.fixture(scope="module")
def con(tmp_path_factory):
    d = tmp_path_factory.mktemp("fresh")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "generate.py"), str(d)], check=True, capture_output=True)
    return connect(d)


def same(a, b) -> bool:
    if len(a) != len(b):
        return False
    for ra, rb in zip(a, b):
        if len(ra) != len(rb):
            return False
        for x, y in zip(ra, rb):
            if isinstance(x, float) or isinstance(y, float):
                if x is None or y is None or not math.isclose(float(x), float(y), abs_tol=0.0011):
                    return False
            elif str(x) != str(y):
                return False
    return True


@pytest.mark.parametrize("name", [
    "q1_weekly_volume_by_driver.sql", "q2_weekly_aht.sql", "q3_fcr_repeat.sql", "q4_abandon_by_interval.sql",
])
def test_matches_reference(con, name):
    _, want = run_file(con, HERE / "ref" / name)
    cols, got = run_file(con, ROOT / "queries" / name)
    assert same(got, want), f"{name}: {len(got)} rows vs reference {len(want)}; first diff near {next((i for i, (x, y) in enumerate(zip(got, want)) if not same([x], [y])), 'length')}"


def test_q1_uses_local_weeks(con):
    _, rows = run_file(con, ROOT / "queries" / "q1_weekly_volume_by_driver.sql")
    assert {str(r[0]) for r in rows} == {"2026-08-24", "2026-08-31", "2026-09-07", "2026-09-14", "2026-09-21", "2026-09-28"}


def test_q2_excludes_abandons(con):
    _, rows = run_file(con, ROOT / "queries" / "q2_weekly_aht.sql")
    assert min(r[2] for r in rows) > 300


def test_q4_local_business_hours(con):
    _, rows = run_file(con, ROOT / "queries" / "q4_abandon_by_interval.sql")
    starts = [r[0] for r in rows]
    assert starts[0] == "06:00" and "09:00" in starts
    peak = max(rows, key=lambda r: r[3])
    assert peak[0] in ("08:00", "08:30", "09:00", "09:30")


def test_q5_runs_and_mentions_the_driver(con):
    cols, rows = run_file(con, ROOT / "queries" / "q5_daily_driver_vs_changes.sql")
    assert len(rows) >= 20 and len(cols) >= 2


def test_findings_root_cause():
    f = json.loads((ROOT / "findings.json").read_text())
    assert f["driver"] == "password_reset"
    assert f["change_id"] == "CHG0031877"
    assert str(f["change_date"]) == "2026-09-21"


def test_findings_numbers():
    f = json.loads((ROOT / "findings.json").read_text())
    assert abs(float(f["pre_fcr_rate"]) - 0.815) <= 0.012
    assert abs(float(f["post_fcr_rate"]) - 0.624) <= 0.012
    assert 1110 <= float(f["excess_contacts_per_week"]) <= 1450
