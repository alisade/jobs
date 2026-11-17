from pathlib import Path

import diffs
import pr_guard

INCIDENT = (Path(__file__).resolve().parent.parent / "incident" / "pr-1187.diff").read_text()


def test_production_only_change_passes():
    assert pr_guard.check(diffs.PRODUCTION_ONLY) == []


def test_deleted_test_file_blocked():
    d = diffs.mk(diffs.TEST, ["class PremiumCalculatorTest {", "}"], [], header_extra="deleted file mode 100644\n")
    assert "test-deleted" in {v.rule for v in pr_guard.check(d)}


def test_incident_pr_is_blocked():
    assert pr_guard.check(INCIDENT), "PR #1187 must not pass the guard"
