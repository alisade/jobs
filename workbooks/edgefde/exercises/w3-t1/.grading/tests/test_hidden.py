"""Hidden tests for edgefde/w3-t1: the gate fails closed and binds metrics to version + holdout."""

import pickle
import sys

from conftest import NAME, run


def pinned(data):
    return (data / "pinned_holdout_sha.txt").read_text().strip()


def gate(data, v):
    return run([sys.executable, "-m", "ci.gate", "--data", str(data), "--model", NAME, "--challenger", str(v)])


def test_evaluate_fails_loudly_on_v7(data, reg):
    r = run([sys.executable, "-m", "ci.evaluate", "--data", str(data), "--model", NAME, "--version", "7"])
    assert r.returncode != 0
    assert reg.get_version(NAME, 7)["metrics"] == []


def test_gate_refuses_unevaluated_challenger(data, reg):
    r = gate(data, 7)
    assert r.returncode == 2, r.stdout + r.stderr
    assert reg.get_alias(NAME, "champion") == 6


def test_gate_refuses_metrics_from_another_holdout(data, reg):
    reg.log_metrics(NAME, 7, "0" * 64, {"recall": 0.99, "false_alarm_rate": 0.001})
    assert gate(data, 7).returncode == 2
    assert reg.get_alias(NAME, "champion") == 6


def test_better_challenger_still_promoted(data, reg):
    v = reg.register(NAME, reg.get_version(NAME, 6)["artifact"], "run-413", "x")
    champ = reg.metrics_for(NAME, 6, pinned(data))
    reg.log_metrics(NAME, v, pinned(data), {"recall": champ["recall"] + 0.02, "false_alarm_rate": champ["false_alarm_rate"]})
    assert gate(data, v).returncode == 0
    assert reg.get_alias(NAME, "champion") == v
    assert reg.get_alias(NAME, "previous-champion") == 6


def test_tie_rejected_end_to_end(data, reg):
    v = reg.register(NAME, reg.get_version(NAME, 6)["artifact"], "run-414", "x")  # same model re-registered
    r = run(["bash", "ci/pipeline.sh", str(data), str(v)])
    assert reg.get_alias(NAME, "champion") == 6, r.stdout
    assert r.returncode != 0


def test_worse_challenger_rejected(data, reg):
    v = reg.register(NAME, reg.get_version(NAME, 6)["artifact"], "run-415", "x")
    champ = reg.metrics_for(NAME, 6, pinned(data))
    reg.log_metrics(NAME, v, pinned(data), {"recall": champ["recall"] + 0.05, "false_alarm_rate": champ["false_alarm_rate"] + 0.01})
    assert gate(data, v).returncode == 3
    assert reg.get_alias(NAME, "champion") == 6


def test_correctly_built_v2_model_promotes_through_pipeline(data, reg):
    """A schema-v2 model evaluated on a schema-v2 holdout is judged on its own numbers (guard)."""
    import numpy as np

    from features import to_v2_schema

    t = to_v2_schema(dict(np.load(data / "holdout.npz")))
    np.savez(data / "holdout.npz", **t)
    import hashlib

    (data / "pinned_holdout_sha.txt").write_text(hashlib.sha256((data / "holdout.npz").read_bytes()).hexdigest())
    # champion v6 cannot read schema v2 either, so the gate must refuse rather than promote blindly
    r = run(["bash", "ci/pipeline.sh", str(data), "7"])
    assert r.returncode != 0 and reg.get_alias(NAME, "champion") == 6
