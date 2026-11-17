"""Visible checks for platform/w5-t1. The hidden suite replays more scenarios."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import eval_rules  # noqa: E402
import gen_tsdb  # noqa: E402
import promql_mini as pm  # noqa: E402

RULES = ROOT / "rules" / "riq-slo.rules.yaml"


def test_promql_mini_smoke():
    db = pm.TSDB()
    for t in range(0, 601, 30):
        db.add({"__name__": "c", "job": "a", "code": "200"}, t, t * 2.0)
        db.add({"__name__": "c", "job": "a", "code": "503"}, t, t * 0.1)
    r = pm.query('sum by (job) (rate(c{code=~"5.."}[5m])) / sum by (job) (rate(c[5m]))', db, 600)
    assert len(r) == 1 and r[0][0] == {"job": "a"} and abs(r[0][1] - 0.1 / 2.1) < 1e-9


def test_rule_file_parses():
    groups = eval_rules.load_rules(str(RULES))
    alerts = [r["alert"] for g in groups for r in g["rules"] if "alert" in r]
    assert "RiqApiErrorBudgetBurnFast" in alerts and "RiqApiErrorBudgetBurnSlow" in alerts


def test_incident_pages():
    db = pm.TSDB.from_json(gen_tsdb.gen("incident"))
    lo, hi = eval_rules.time_range(db)
    events = eval_rules.run(eval_rules.load_rules(str(RULES)), db, lo, hi)
    fast = [e for e in events if e["alert"] == "RiqApiErrorBudgetBurnFast"]
    assert fast, "the fast-burn alert did not fire during the 2026-11-04 outage"
