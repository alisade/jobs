"""Hidden tests for healthai/w1-t1: the fixed clock, the regenerated numbers, and findings.json."""

import csv
import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from clockreport.deadlines import decision_deadline
from clockreport.report import IMPACTED, build

EX = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def data(tmp_path_factory):
    d = tmp_path_factory.mktemp("data")
    subprocess.run([sys.executable, str(EX / "scripts" / "generate.py"), str(d)], check=True, capture_output=True, timeout=60)
    return d


def truth(cases_csv):
    late = {"expedited": [], "standard": []}
    for r in csv.DictReader(open(cases_csv)):
        if r["lob"] not in IMPACTED:
            continue
        rec = datetime.fromisoformat(r["received_at"])
        if r["priority"] == "expedited":
            due = rec.astimezone(UTC) + timedelta(hours=72)
        else:
            z = ZoneInfo(r["plan_tz"])
            loc = rec.astimezone(z)
            due = (loc.replace(tzinfo=None) + timedelta(days=7)).replace(tzinfo=z).astimezone(UTC)
        if datetime.fromisoformat(r["decided_at"]) > due:
            late[r["priority"]].append(r["case_id"])
    return late


def test_standard_is_seven_calendar_days_from_friday():
    rec = datetime(2026, 11, 13, 16, 0, tzinfo=timezone(timedelta(hours=-6)))  # Friday, Chicago
    assert decision_deadline(rec, "standard", "America/Chicago") == datetime(2026, 11, 20, 22, 0, tzinfo=UTC)


def test_standard_weekend_receipt():
    rec = datetime(2026, 11, 14, 10, 0, tzinfo=timezone(timedelta(hours=-7)))  # Saturday, Denver
    assert decision_deadline(rec, "standard", "America/Denver") == datetime(2026, 11, 21, 17, 0, tzinfo=UTC)


def test_standard_across_fall_back_keeps_local_time():
    rec = datetime(2026, 10, 28, 9, 0, tzinfo=timezone(timedelta(hours=-4)))
    assert decision_deadline(rec, "standard", "America/New_York") == datetime(2026, 11, 4, 14, 0, tzinfo=UTC)


def test_expedited_unchanged_guard():
    rec = datetime(2026, 11, 13, 16, 0, tzinfo=timezone(timedelta(hours=-6)))
    assert decision_deadline(rec, "expedited", "America/Chicago") == datetime(2026, 11, 16, 22, 0, tzinfo=UTC)


def test_report_late_counts_match_truth(data):
    out = build(data / "cases.csv")
    t = truth(data / "cases.csv")
    assert out["standard"]["late"] == len(t["standard"]) > 0
    assert out["expedited"]["late"] == len(t["expedited"])
    assert out["late_case_ids"] == sorted(t["standard"] + t["expedited"])


def test_audit_sample_cases_are_reported_late(data):
    out = build(data / "cases.csv")
    sample = [r["case_id"] for r in csv.DictReader(open(data / "audit_sample.csv"))]
    assert set(sample) <= set(out["late_case_ids"])


def test_findings_json(data):
    f = json.loads((EX / "findings.json").read_text())
    t = truth(data / "cases.csv")
    sample = sorted(r["case_id"] for r in csv.DictReader(open(data / "audit_sample.csv")))
    assert "deadlines.py" in f["root_cause_file"]
    assert f["root_cause_function"] in ("add_days", "decision_deadline")
    assert f["late_standard_decisions"] == len(t["standard"])
    assert f["late_expedited_decisions"] == len(t["expedited"])
    assert sorted(f["audit_sample_confirmed"]) == sample
