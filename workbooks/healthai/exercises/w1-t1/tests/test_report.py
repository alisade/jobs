"""Visible tests: the report runs and the expedited clock is right."""

from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

from clockreport.deadlines import decision_deadline
from clockreport.report import build

DATA = Path(__file__).resolve().parent.parent / "data" / "cases.csv"


def test_expedited_deadline_is_72_hours():
    rec = datetime(2026, 10, 30, 22, 15, tzinfo=timezone(timedelta(hours=-4)))
    assert decision_deadline(rec, "expedited", "America/New_York") == datetime(2026, 11, 3, 2, 15, tzinfo=UTC)


def test_standard_deadline_monday_receipt():
    rec = datetime(2026, 11, 9, 9, 0, tzinfo=timezone(timedelta(hours=-5)))  # Monday 09:00 EST
    assert decision_deadline(rec, "standard", "America/New_York") == datetime(2026, 11, 16, 14, 0, tzinfo=UTC)


def test_report_runs_on_the_export():
    out = build(DATA)
    assert out["expedited"]["total"] > 0 and out["standard"]["total"] > 0
