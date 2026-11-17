"""Hidden tests for audit/w6-t1: restored human ground truth, provenance refusal, safe refresh."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys

import pytest

from conftest import ROOT
from harness.golden import ProvenanceError, load_golden, load_runs
from harness.score import score


def rows(path):
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


HUMAN = {r["sample_id"]: r for r in rows(ROOT / "labels" / "human_v1" / "cm03-golden-v1.jsonl")}


def test_human_v1_untouched():
    assert len(HUMAN) == 30
    assert all(r["labeled_by"].startswith("human:") for r in HUMAN.values())
    assert sum(r["overall"] == "exception" for r in HUMAN.values()) == 7


def test_golden_is_the_human_labels():
    g = {r["sample_id"]: r for r in rows(ROOT / "labels" / "golden.jsonl")}
    assert set(g) == set(HUMAN)
    for sid, h in HUMAN.items():
        assert g[sid]["labels"] == h["labels"], sid
        assert g[sid]["overall"] == h["overall"], sid
        assert g[sid]["labeled_by"] == h["labeled_by"], sid
        assert g[sid]["labeled_at"] == h["labeled_at"], sid
        assert g[sid]["control_id"] == "CM-03"


def test_true_dashboard_numbers():
    s = score(load_golden(ROOT / "labels" / "golden.jsonl"), load_runs(ROOT / "runs" / "2026Q3" / "production.jsonl"))
    assert s["accuracy"] == pytest.approx(26 / 30)
    assert s["exception_recall"] == pytest.approx(3 / 7)
    assert s["missed_exceptions"] == ["Q3-03", "Q3-11", "Q3-19", "Q3-26"]


def _write(path, recs):
    path.write_text("".join(json.dumps(r) + "\n" for r in recs))


def _row(sid, by):
    return {"sample_id": sid, "change_id": "CHG-100001", "control_id": "CM-03", "labels": {}, "overall": "pass",
            "labeled_by": by, "labeled_at": "2026-07-01T00:00:00Z"}


def test_loader_refuses_model_labels(tmp_path):
    p = tmp_path / "g.jsonl"
    _write(p, [_row("A", "human:r.okafor"), _row("B", "model:gemini-3.8-flash")])
    with pytest.raises(ProvenanceError):
        load_golden(p)


@pytest.mark.parametrize("by", ["", "unknown", "agent:controlpilot", "Model:gemini"])
def test_loader_refuses_non_human(tmp_path, by):
    p = tmp_path / "g.jsonl"
    _write(p, [_row("A", by)])
    with pytest.raises(ProvenanceError):
        load_golden(p)


def test_loader_accepts_human_and_still_requires_schema(tmp_path):
    p = tmp_path / "g.jsonl"
    _write(p, [_row("A", "human:s.lindqvist")])
    assert set(load_golden(p)) == {"A"}
    bad = _row("A", "human:s.lindqvist")
    del bad["control_id"]
    _write(p, [bad])
    with pytest.raises(ValueError):
        load_golden(p)


def test_cli_refuses_the_broken_golden_set(tmp_path):
    p = tmp_path / "g.jsonl"
    _write(p, [_row(f"Q3-{i:02d}", "model:gemini-3.8-flash") for i in range(1, 31)])
    r = subprocess.run([sys.executable, "-m", "harness.cli", "--golden", str(p)], cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert r.returncode != 0
    assert "accuracy" not in r.stdout or "%" not in r.stdout


def _copy(tmp_path):
    dst = tmp_path / "ex"
    shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns("__pycache__", "tests", "tests_hidden", "incident"))
    return dst


def test_refresh_golden_never_rewrites_labels(tmp_path):
    ex = _copy(tmp_path)
    r = subprocess.run([sys.executable, "scripts/refresh_golden.py"], cwd=ex, capture_output=True, text=True, timeout=60)
    g = {x["sample_id"]: x for x in rows(ex / "labels" / "golden.jsonl")}
    assert all(x["labeled_by"].startswith("human:") for x in g.values()), r.stdout + r.stderr
    for sid, h in HUMAN.items():
        assert g[sid]["overall"] == h["overall"] and g[sid]["labels"] == h["labels"]


def test_refresh_golden_does_not_turn_model_rows_into_labels(tmp_path):
    ex = _copy(tmp_path)
    # a v1 file (no control_id) with one model-labeled row sneaking in
    v1 = [dict(h) for h in HUMAN.values()]
    v1[0] = dict(v1[0], labeled_by="model:gemini-3.8-flash")
    _write(ex / "labels" / "golden.jsonl", v1)
    r = subprocess.run([sys.executable, "scripts/refresh_golden.py"], cwd=ex, capture_output=True, text=True, timeout=60)
    after = rows(ex / "labels" / "golden.jsonl")
    model_rows = [x for x in after if not str(x.get("labeled_by", "")).startswith("human:")]
    assert r.returncode != 0 or not model_rows, "refresh-golden accepted or produced model-labeled ground truth"
    assert len([x for x in after if x["overall"] == "exception"]) >= 6
