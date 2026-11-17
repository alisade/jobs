"""Hidden tests for audit/w2-c1."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date

import pytest
from conftest import END, ROOT, START

from sampling.population import (accuracy_checks, build_population, completeness, population_hash,
                                 sample_size, select_sample, selection_log)


def D(cid, ts, env="prod", status="succeeded", pr=1):
    return {"change_id": cid, "pr_number": pr, "repo": "mfh/x", "environment": env, "deployed_at": ts,
            "pipeline_run": "r", "status": status}


PRS = [{"number": 1, "repo": "mfh/x", "base": "main", "merged_at": "2025-12-30T00:00:00Z", "change_id": "CHG-1", "author": "a"}]


def ids(pop):
    return [i.change_id for i in pop]


def test_local_date_boundaries():
    deploys = [D("CHG-A", "2026-01-01T05:30:00Z"), D("CHG-B", "2026-01-01T06:30:00Z"),
               D("CHG-C", "2026-10-01T03:30:00Z"), D("CHG-D", "2026-10-01T05:10:00Z")]
    assert ids(build_population(PRS, deploys, START, END)) == ["CHG-B", "CHG-C"]


def test_status_and_environment_filters():
    deploys = [D("CHG-A", "2026-03-01T12:00:00Z", status="failed"), D("CHG-B", "2026-03-01T12:00:00Z", env="staging"),
               D("CHG-C", "2026-03-01T12:00:00Z", status="rolled_back"), D("CHG-E", "2026-03-01T12:00:00Z")]
    assert ids(build_population(PRS, deploys, START, END)) == ["CHG-C", "CHG-E"]


def test_redeploys_collapse_to_the_first():
    deploys = [D("CHG-A", "2026-03-01T15:00:00Z"), D("CHG-A", "2026-03-01T12:00:00Z")]
    pop = build_population(PRS, deploys, START, END)
    assert len(pop) == 1 and pop[0].deploy_count == 2 and pop[0].first_deployed_at == "2026-03-01T12:00:00Z"
    assert pop[0].local_date == "2026-03-01"


def test_unmerged_change_stays_in_the_population(ex):
    pop = build_population(ex["prs"], ex["deploys"], START, END)
    by = {i.change_id: i for i in pop}
    assert "CHG-100264" in by and by["CHG-100264"].pr_merged_to_main is False
    assert "CHG-100265" in by and by["CHG-100265"].pr_merged_to_main is False


def test_population_sorted_and_real_counts(ex):
    pop = build_population(ex["prs"], ex["deploys"], START, END)
    assert ids(pop) == sorted(ids(pop))
    assert len(pop) == 220


def test_completeness_detects_a_gap(ex):
    pop = build_population(ex["prs"], ex["deploys"], START, END)
    rec = completeness(pop[:-3], ex["total"])
    assert not rec.reconciled and rec.differences


def test_accuracy_findings(ex):
    pop = build_population(ex["prs"], ex["deploys"], START, END)
    issues = " | ".join(accuracy_checks(pop, ex["prs"], ex["tickets"]))
    for cid in ("CHG-100264", "CHG-100265", "CHG-100266"):
        assert cid in issues
    assert len(accuracy_checks(pop, ex["prs"], ex["tickets"])) == 3


def test_accuracy_merged_after_deploy():
    prs = [dict(PRS[0], merged_at="2026-03-02T00:00:00Z")]
    pop = build_population(prs, [D("CHG-1", "2026-03-01T12:00:00Z")], START, END)
    assert any("after" in s for s in accuracy_checks(pop, prs, [{"change_id": "CHG-1", "state": "closed", "risk": "low"}]))


@pytest.mark.parametrize("freq,risk,n", [("annual", "standard", 1), ("quarterly", "high", 2), ("monthly", "high", 3),
                                         ("weekly", "standard", 5), ("daily", "high", 40), ("recurring", "high", 40)])
def test_sample_size_table(ex, freq, risk, n):
    assert sample_size(ex["table"], freq, risk) == n


def test_sample_size_unknown_frequency(ex):
    with pytest.raises(ValueError):
        sample_size(ex["table"], "fortnightly")


def test_selection_is_reproducible_and_order_independent(ex):
    pop = build_population(ex["prs"], ex["deploys"], START, END)
    a = select_sample(pop, 25, 20261005)
    b = select_sample(list(reversed(pop)), 25, 20261005)
    assert ids(a) == ids(b) and len(set(ids(a))) == 25
    c = select_sample(pop, 25, 7)
    assert ids(a) != ids(c)


def test_selection_matches_documented_method(ex):
    import random
    pop = build_population(ex["prs"], ex["deploys"], START, END)
    ordered = sorted(ids(pop))
    expect = [ordered[k] for k in random.Random(99).sample(range(len(ordered)), 10)]
    assert ids(select_sample(pop, 10, 99)) == expect


def test_small_population_takes_everything():
    pop = build_population(PRS, [D("CHG-1", "2026-03-01T12:00:00Z"), D("CHG-2", "2026-03-02T12:00:00Z")], START, END)
    assert sorted(ids(select_sample(pop, 25, 1))) == ["CHG-1", "CHG-2"]


def test_population_hash_is_order_independent(ex):
    pop = build_population(ex["prs"], ex["deploys"], START, END)
    h = population_hash(pop)
    assert h == population_hash(list(reversed(pop))) and len(h) == 64
    assert h != population_hash(pop[1:])


def test_selection_log_fields(ex):
    pop = build_population(ex["prs"], ex["deploys"], START, END)
    rec = completeness(pop, ex["total"])
    s = select_sample(pop, 25, 5)
    log = selection_log(pop, s, 5, 25, "recurring", "standard", rec, [])
    json.dumps(log)
    assert log["seed"] == 5 and log["population_count"] == 220 and log["selected"] == ids(s)
    assert log["population_sha256"] == population_hash(pop)
    assert log["completeness"]["reconciled"] is True


def test_select_script_runs(tmp_path):
    import shutil
    work = tmp_path / "w"
    shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    r = subprocess.run([sys.executable, "select.py", "11"], cwd=work, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    assert json.loads((work / "selection_log.json").read_text())["seed"] == 11
