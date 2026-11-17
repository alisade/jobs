import json
from pathlib import Path

import pytest

import remediate

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def rep():
    return remediate.build_report(remediate.parse_sbom(ROOT / "sbom/before.cdx.json"),
                                  remediate.parse_sbom(ROOT / "sbom/after.cdx.json"),
                                  remediate.load_advisories(ROOT / "advisories"))


@pytest.mark.parametrize("a,b,sign", [
    ("2.9.8", "2.9.10.8", -1), ("1.9", "1.10.0", -1), ("4.1.94.Final", "4.1.100.Final", -1),
    ("10.1.34", "9.0.98", 1), ("3.12.0", "3.10", 1), ("1.0.0", "1.0", 0), ("1.0.Final", "1.0", 0),
    ("2.2.3.Final", "2.2.3.Final", 0), ("1.0-RC1", "1.0", -1), ("1.0-rc1", "1.0-rc2", -1),
    ("1.0-SNAPSHOT", "1.0", -1), ("2.0-beta9", "2.0", -1), ("1.0-beta", "1.0-RC1", -1),
])
def test_compare_versions(a, b, sign):
    c = remediate.compare_versions(a, b)
    assert (c > 0) - (c < 0) == sign, f"compare_versions({a!r}, {b!r}) = {c}"
    c2 = remediate.compare_versions(b, a)
    assert (c2 > 0) - (c2 < 0) == -sign, "comparison must be antisymmetric"


TOMCAT = [{"type": "ECOSYSTEM", "events": [{"introduced": "9.0.0"}, {"fixed": "9.0.98"}]},
          {"type": "ECOSYSTEM", "events": [{"introduced": "10.1.0"}, {"fixed": "10.1.34"}]},
          {"type": "ECOSYSTEM", "events": [{"introduced": "11.0.0"}, {"fixed": "11.0.2"}]}]


@pytest.mark.parametrize("v,hit", [("9.0.83", True), ("9.0.98", False), ("10.1.20", True), ("10.1.34", False),
                                   ("10.1.100", False), ("8.5.99", False), ("11.0.1", True), ("11.0.10", False)])
def test_multiple_ranges(v, hit):
    assert remediate.is_affected(v, TOMCAT) is hit


EXPECTED = {
    "CMV-2026-0101": "remaining", "CMV-2026-0102": "remaining", "CMV-2026-0103": "fixed",
    "CMV-2026-0104": "fixed", "CMV-2026-0105": "fixed", "CMV-2026-0106": "remaining",
    "CMV-2026-0107": "introduced", "CMV-2026-0108": "not-affected", "CMV-2026-0109": "not-affected",
}


def test_report_statuses(rep):
    got = {f["advisory"]: f["status"] for f in rep["findings"]}
    assert got == EXPECTED


def test_report_summary(rep):
    s = rep["summary"]
    assert (s["fixed"], s["remaining"], s["introduced"]) == (3, 3, 1)
    assert s["open_by_severity"]["CRITICAL"] == 2 and s["open_by_severity"]["HIGH"] == 2


def test_gate_fails_on_open_criticals(tmp_path):
    rc = remediate.main(["--before", str(ROOT / "sbom/before.cdx.json"), "--after", str(ROOT / "sbom/after.cdx.json"),
                         "--advisories", str(ROOT / "advisories"), "--out", str(tmp_path), "--fail-on", "CRITICAL"])
    assert rc == 1
    assert json.loads((tmp_path / "report.json").read_text())["summary"]["open_by_severity"]["CRITICAL"] == 2


def test_gate_passes_when_criticals_closed(tmp_path):
    after = json.loads((ROOT / "sbom/after.cdx.json").read_text())
    for c in after["components"]:
        if c["name"] == "jackson-databind":
            c["version"] = "2.13.4.2"
        if c["name"] == "commons-text":
            c["version"] = "1.10.0"
    p = tmp_path / "after.json"
    p.write_text(json.dumps(after))
    rc = remediate.main(["--before", str(ROOT / "sbom/before.cdx.json"), "--after", str(p),
                         "--advisories", str(ROOT / "advisories"), "--out", str(tmp_path / "out"), "--fail-on", "CRITICAL"])
    assert rc == 0
