from pathlib import Path

import remediate

ROOT = Path(__file__).resolve().parent.parent


def report():
    return remediate.build_report(remediate.parse_sbom(ROOT / "sbom/before.cdx.json"),
                                  remediate.parse_sbom(ROOT / "sbom/after.cdx.json"),
                                  remediate.load_advisories(ROOT / "advisories"))


def status(rep, pkg_suffix):
    return [f["status"] for f in rep["findings"] if f["package"].endswith(pkg_suffix)][0]


def test_sbom_parsing():
    after = remediate.parse_sbom(ROOT / "sbom/after.cdx.json")
    assert after["org.apache.logging.log4j:log4j-core"] == "2.17.1"
    assert "org.apache.commons:commons-compress" in after


def test_log4j_upgrade_is_fixed():
    assert status(report(), ":log4j-core") == "fixed"


def test_multi_digit_components():
    assert remediate.compare_versions("1.9", "1.10.0") < 0


def test_version_semantics():
    assert remediate.compare_versions("2.9.8", "2.9.10.8") < 0
    assert remediate.compare_versions("1.0.Final", "1.0") == 0
    assert remediate.compare_versions("1.0-RC1", "1.0") < 0


def test_scanner_criticals_are_open():
    rep = report()
    assert status(rep, ":jackson-databind") == "remaining"
    assert status(rep, ":commons-text") == "remaining"
    assert rep["summary"]["open_by_severity"]["CRITICAL"] == 2
