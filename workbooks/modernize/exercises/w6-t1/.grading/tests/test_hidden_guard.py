from pathlib import Path

import pytest

import diffs
import pr_guard

ROOT = Path(__file__).resolve().parent.parent
INCIDENT = (ROOT / "incident" / "pr-1187.diff").read_text()
T, G, M = diffs.TEST, diffs.GOLDEN, diffs.MAIN


def rules(diff, labels=frozenset()):
    return sorted(v.rule for v in pr_guard.check(diff, labels))


# ---------- the incident ----------

def test_incident_violations_exact():
    assert rules(INCIDENT) == ["golden-changed", "golden-changed", "test-disabled"]


def test_incident_with_golden_label_still_blocked_by_disabled_test():
    assert rules(INCIDENT, frozenset({"approved-golden-change"})) == ["test-disabled"]


# ---------- violations ----------

def test_assertion_removed():
    d = diffs.mk(T, ['        assertEquals(new BigDecimal("5113.18"), calc.premium(c, r));'], [])
    assert "assertion-removed" in rules(d)


def test_test_method_removed_drops_count():
    d = diffs.mk(T, ["    @Test", "    void roundsHalfCentUp() {", '        assertEquals(a, b);', "    }"], [])
    r = rules(d)
    assert "test-count-dropped" in r and "assertion-removed" in r


def test_deleted_test_file_reports_all_rules():
    d = diffs.mk(T, ["    @Test", "    void a() {", "        assertEquals(1, 1);", "    }"], [], header_extra="deleted file mode 100644\n")
    assert {"test-deleted", "test-count-dropped", "assertion-removed"} <= set(rules(d))


@pytest.mark.parametrize("path,line", [
    ("claimdesk-intake/tests/test_parser.py", "@pytest.mark.skip(reason='later')"),
    ("claimdesk-intake/tests/test_parser.py", "    pytest.skip('broken on CI')"),
    ("policy-portal/tests/Rating.Tests/PremiumTests.cs", '    [Fact(Skip = "flaky")]'),
    ("claimdesk-rating/src/test/java/x/LegacyTest.java", "    @Ignore"),
])
def test_skip_markers_in_other_frameworks(path, line):
    assert "test-disabled" in rules(diffs.mk(path, [], [line]))


def test_new_golden_file_needs_label():
    d = diffs.mk("claimdesk-rating/src/test/resources/golden/bordereau-2026-11.json", [], ['[{"claim": "X"}]'],
                 header_extra="new file mode 100644\n", old="dev/null")
    assert rules(d) == ["golden-changed"]


def test_approval_test_files_count_as_golden():
    d = diffs.mk("claimdesk-notes/src/test/java/x/FlowTest.get_claim.approved.txt", ["status: 200"], ["status: 201"])
    assert rules(d) == ["golden-changed"]


def test_every_violation_reported_not_just_the_first():
    assert len(pr_guard.check(INCIDENT)) == 3


# ---------- clean changes must pass ----------

def test_assertion_moved_within_file_passes():
    d = diffs.mk(T, ["        assertEquals(a, calc.premium(c, r));"], ["        assertEquals(a, calc.premium(c, rate));"])
    assert rules(d) == []


def test_new_test_passes():
    d = diffs.mk(T, [], ["    @Test", "    void roundsHalfCentUpOnCommission() {", "        assertEquals(x, y);", "    }"])
    assert rules(d) == []


def test_removing_a_disable_passes():
    assert rules(diffs.mk(T, ['    @Disabled("flaky")'], [])) == []


def test_golden_change_with_label_passes():
    d = diffs.mk(G, ['  {"commission": "70.13"}'], ['  {"commission": "70.14"}'])
    assert rules(d, frozenset({"approved-golden-change"})) == []


def test_golden_looking_name_in_main_code_passes():
    d = diffs.mk("claimdesk-rating/src/main/java/x/GoldenRatioDiscount.java", ["int a = 1;"], ["int a = 2;"])
    assert rules(d) == []


def test_pure_rename_of_test_file_passes():
    d = ("diff --git a/claimdesk-rating/src/test/java/x/OldNameTest.java b/claimdesk-rating/src/test/java/x/NewNameTest.java\n"
         "similarity index 100%\nrename from claimdesk-rating/src/test/java/x/OldNameTest.java\n"
         "rename to claimdesk-rating/src/test/java/x/NewNameTest.java\n")
    assert rules(d) == []


def test_comment_mentioning_disabled_passes():
    assert rules(diffs.mk(T, [], ["    // never add @Disabled here: treaty clause 7.2 (INC-7790)"])) == []


def test_import_of_disabled_alone_passes():
    assert rules(diffs.mk(T, [], ["import org.junit.jupiter.api.Disabled;"])) == []


# ---------- CLI ----------

def test_cli_exit_codes(tmp_path, capsys):
    bad = tmp_path / "bad.diff"
    bad.write_text(INCIDENT)
    good = tmp_path / "good.diff"
    good.write_text(diffs.PRODUCTION_ONLY)
    assert pr_guard.main([str(bad)]) == 1
    assert pr_guard.main([str(bad), "--label", "approved-golden-change"]) == 1
    assert pr_guard.main([str(good)]) == 0
    assert pr_guard.main([str(tmp_path / "missing.diff")]) == 2
