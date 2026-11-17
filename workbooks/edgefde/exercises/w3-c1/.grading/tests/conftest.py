from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")  # single-row latency is meaningless with oversubscribed thread pools

import shutil
import sys
import warnings
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
warnings.filterwarnings("ignore")


@pytest.fixture(scope="session")
def built(tmp_path_factory):
    import data

    out = tmp_path_factory.mktemp("built")
    return data.build(out)


@pytest.fixture
def env(built, tmp_path):
    """A fresh registry copy per test (artifacts and holdout shared, read-only)."""
    from mlreg.registry import FileRegistry

    shutil.copytree(built["out"] / "registry", tmp_path / "registry")
    return {"reg": FileRegistry(tmp_path / "registry"), "holdout": built["out"] / "holdout.npz",
            "sha": built["holdout_sha"], "tmp": tmp_path, "out": built["out"]}
