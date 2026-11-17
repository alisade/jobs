"""Visible: replaying build #412 must not promote v7; the champion still evaluates."""

import sys

from conftest import NAME, run


def test_build_412_does_not_promote_v7(data, reg):
    r = run(["bash", "ci/pipeline.sh", str(data), "7"])
    assert reg.get_alias(NAME, "champion") == 6, r.stdout + r.stderr
    assert r.returncode != 0, "the pipeline must fail, not finish green"


def test_champion_still_evaluates(data, reg):
    r = run([sys.executable, "-m", "ci.evaluate", "--data", str(data), "--model", NAME, "--version", "6"])
    assert r.returncode == 0, r.stderr
