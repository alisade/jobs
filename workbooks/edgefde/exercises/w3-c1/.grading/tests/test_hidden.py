"""Hidden tests for edgefde/w3-c1."""

import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from gate import gate as G  # noqa: E402

NAME = "pump-anomaly"


def champion(env, v=1):
    assert G.promote(env["reg"], NAME, v, env["holdout"], env["sha"]) == G.PROMOTED


def test_better_challenger_moves_alias_and_keeps_previous(env):
    champion(env, 1)
    code = G.promote(env["reg"], NAME, 2, env["holdout"], env["sha"], comment_path=env["tmp"] / "c.md")
    assert code == G.PROMOTED
    assert env["reg"].get_alias(NAME, "champion") == 2
    assert env["reg"].get_alias(NAME, "previous-champion") == 1


def test_worse_false_alarms_rejected_aliases_unchanged(env):
    champion(env, 1)
    G.promote(env["reg"], NAME, 2, env["holdout"], env["sha"])
    code = G.promote(env["reg"], NAME, 3, env["holdout"], env["sha"])
    assert code == G.REJECTED
    assert env["reg"].get_alias(NAME, "champion") == 2


def test_tie_is_rejected(env):
    champion(env, 2)
    art = env["reg"].get_version(NAME, 2)["artifact"]
    v = env["reg"].register(NAME, art, "run-dup", "x")
    assert G.promote(env["reg"], NAME, v, env["holdout"], env["sha"]) == G.REJECTED


def test_decide_recall_up_far_worse_rejected():
    champ = G.Metrics(0.64, 0.020, 1.0, 300, 2700)
    chal = G.Metrics(0.75, 0.025, 1.0, 300, 2700)
    d = G.decide(champ, chal)
    assert not d.promote and d.reasons


def test_floors_apply_to_first_model(env):
    assert G.promote(env["reg"], NAME, 3, env["holdout"], env["sha"]) == G.REJECTED  # FAR ~0.05 > 0.03
    assert env["reg"].get_alias(NAME, "champion") is None


def test_latency_budget(env):
    code = G.promote(env["reg"], NAME, 1, env["holdout"], env["sha"], rules=G.Rules(max_p95_latency_ms=1e-6))
    assert code == G.REJECTED


def test_holdout_hash_mismatch_fails_closed(env):
    champion(env, 1)
    with pytest.raises(G.GateError):
        G.promote(env["reg"], NAME, 2, env["holdout"], "0" * 64)
    assert env["reg"].get_alias(NAME, "champion") == 1


def test_missing_artifact_fails_closed(env):
    champion(env, 1)
    v = env["reg"].register(NAME, env["tmp"] / "nope.pkl", "run-x", "x")
    with pytest.raises(G.GateError):
        G.promote(env["reg"], NAME, v, env["holdout"], env["sha"])
    assert env["reg"].get_alias(NAME, "champion") == 1


def test_both_evaluated_fresh_on_same_holdout(env):
    champion(env, 1)
    G.promote(env["reg"], NAME, 2, env["holdout"], env["sha"])
    for v in (1, 2):
        m = env["reg"].metrics_for(NAME, v, env["sha"])
        assert m and 0 <= m["recall"] <= 1 and "false_alarm_rate" in m
    # v1 was evaluated twice (as challenger, then as champion): metrics are appended, not trusted
    assert len(env["reg"].get_version(NAME, 1)["metrics"]) == 2


def test_stale_registry_metrics_are_not_trusted(env):
    """Fake great metrics logged earlier for v3 must not let it through."""
    champion(env, 2)
    env["reg"].log_metrics(NAME, 3, env["sha"], {"recall": 0.99, "false_alarm_rate": 0.0, "p95_latency_ms": 0.1,
                                                   "positives": 1, "negatives": 1})
    assert G.promote(env["reg"], NAME, 3, env["holdout"], env["sha"]) == G.REJECTED


def test_comment_markdown(env):
    champion(env, 1)
    path = env["tmp"] / "comment.md"
    G.promote(env["reg"], NAME, 3, env["holdout"], env["sha"], comment_path=path)
    text = path.read_text()
    assert "Decision: REJECT" in text
    assert "| recall |" in text and "v1" in text and "v3" in text


def test_rollback(env):
    champion(env, 1)
    G.promote(env["reg"], NAME, 2, env["holdout"], env["sha"])
    assert G.rollback(env["reg"], NAME) == G.PROMOTED
    assert env["reg"].get_alias(NAME, "champion") == 1
    with pytest.raises(G.GateError):
        G.rollback(env["reg"], NAME)


def test_cli_exit_codes(env):
    base = [sys.executable, "-m", "gate.gate"]
    reg = str(env["tmp"] / "registry")
    common = ["--registry", reg, "--model", NAME, "--holdout", str(env["holdout"])]
    r = subprocess.run(base + ["promote", *common, "--challenger", "1", "--expected-holdout-sha", env["sha"]],
                       cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    r = subprocess.run(base + ["promote", *common, "--challenger", "3", "--expected-holdout-sha", env["sha"]],
                       cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert r.returncode == 3
    r = subprocess.run(base + ["promote", *common, "--challenger", "2", "--expected-holdout-sha", "f" * 64],
                       cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert r.returncode == 2
    r = subprocess.run(base + ["rollback", "--registry", reg, "--model", NAME],
                       cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert r.returncode == 2  # nothing to roll back to
