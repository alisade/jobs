"""Hidden tests for platform/w5-t1: replay the learner's rule file over several scenarios using the
grader's own copy of the evaluator (tests_hidden/support)."""
import os
import pathlib
import re
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "support"))
import eval_rules  # noqa: E402
import gen_tsdb  # noqa: E402
import promql_mini as pm  # noqa: E402

RULES = pathlib.Path(os.getcwd()) / "rules" / "riq-slo.rules.yaml"
SLO_ALERTS = {"RiqApiErrorBudgetBurnFast", "RiqApiErrorBudgetBurnSlow"}
_cache = {}


def replay(scenario):
    if scenario not in _cache:
        db = pm.TSDB.from_json(gen_tsdb.gen(scenario))
        lo, hi = eval_rules.time_range(db)
        _cache[scenario] = eval_rules.run(eval_rules.load_rules(str(RULES)), db, lo, hi)
    return _cache[scenario]


def t(s):
    return gen_tsdb.ts(s)


def first(events, name):
    hits = [e for e in events if e["alert"] == name]
    return hits[0] if hits else None


def test_incident_fast_burn_pages_within_20_minutes():
    e = first(replay("incident"), "RiqApiErrorBudgetBurnFast")
    assert e, "fast-burn alert never fired during the outage"
    start = t("2026-11-04T13:12:00Z")
    assert start <= e["fired_at"] <= start + 20 * 60, f"fired at {eval_rules.iso(e['fired_at'])}"


def test_incident_alert_routes_as_a_riq_page():
    e = first(replay("incident"), "RiqApiErrorBudgetBurnFast")
    assert e and e["labels"].get("severity") == "page" and e["labels"].get("team") == "riq"
    assert e["labels"].get("job", "riq-api") == "riq-api"


def test_healthy_day_is_quiet():
    assert replay("healthy") == [], [x["alert"] for x in replay("healthy")]


def test_short_spike_does_not_page():
    fired = {e["alert"] for e in replay("spike")}
    assert not (fired & SLO_ALERTS), "a 4-minute spike must not page (multi-window)"


def test_slow_burn_pages_slow_not_fast():
    fired = {e["alert"] for e in replay("slowburn")}
    assert "RiqApiErrorBudgetBurnSlow" in fired, "burn rate 12 for 5 hours must page via the 6h/30m window"
    assert "RiqApiErrorBudgetBurnFast" not in fired, "burn rate 12 is below the 14.4 fast threshold"


def test_burn_16_pages_fast():
    assert first(replay("fastburn16"), "RiqApiErrorBudgetBurnFast"), "burn rate 16 sustained must page fast"


def test_outage_on_second_cluster_pages_within_40_minutes():
    e = first(replay("twoclusters"), "RiqApiErrorBudgetBurnFast")
    assert e, "an outage on prod-green (half the traffic) did not page"
    start = t("2026-11-08T13:00:00Z")
    assert e["fired_at"] <= start + 40 * 60
    if "cluster" in e["labels"]:
        assert e["labels"]["cluster"] == "prod-green"


def test_guard_fires_when_slo_series_disappear():
    drift = replay("drift")
    assert drift, "no alert fired although the riq-api series no longer match the SLO selectors"
    assert not ({e["alert"] for e in drift} & SLO_ALERTS)
    guard = drift[0]
    assert guard["fired_at"] <= t("2026-11-02T06:30:00Z"), "the guard should fire within 30 minutes"


def test_rules_no_longer_depend_on_the_service_label():
    text = RULES.read_text()
    exprs = " ".join(re.findall(r"expr:\s*(.*)", text))
    assert not re.search(r"\bservice\s*[=!]~?\s*\"|by\s*\([^)]*\bservice\b", exprs), "rules still select or group on `service`"
