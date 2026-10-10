"""Visible checks for connect/w2-c3: every query runs and has the documented columns."""

import json

from conftest import ROOT

COLUMNS = {
    "q1_weekly_volume_by_driver.sql": ["week_start", "contact_driver", "contacts"],
    "q2_weekly_aht.sql": ["week_start", "channel", "aht_seconds"],
    "q3_fcr_repeat.sql": ["week_start", "contact_driver", "answered_contacts", "repeat_within_7d", "fcr_rate"],
    "q4_abandon_by_interval.sql": ["interval_start", "offered", "abandoned", "abandon_rate"],
}


def test_columns(q):
    for name, cols in COLUMNS.items():
        got, _ = q(name)
        assert got == cols, name


def test_q1_counts_every_contact(q, con):
    _, rows = q("q1_weekly_volume_by_driver.sql")
    assert sum(r[2] for r in rows) == con.sql("SELECT COUNT(*) FROM contact_records").fetchone()[0]


def test_q3_returns_rows(q):
    _, rows = q("q3_fcr_repeat.sql")
    assert len(rows) > 0


def test_findings_filled_in():
    f = json.loads((ROOT / "findings.json").read_text())
    assert all(f.get(k) is not None for k in ("driver", "change_id", "change_date", "pre_fcr_rate", "post_fcr_rate", "excess_contacts_per_week"))
