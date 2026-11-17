from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import shutil
import subprocess
import sys
import warnings
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
warnings.filterwarnings("ignore")
NAME = "pump-anomaly"


@pytest.fixture(scope="session")
def pristine(tmp_path_factory):
    import build_incident

    d = tmp_path_factory.mktemp("pristine") / "data"
    build_incident.build(d)
    return d


@pytest.fixture
def data(pristine, tmp_path):
    """Registry state just before build #412's evaluate step (v6 champion, v7 registered)."""
    d = tmp_path / "data"
    shutil.copytree(pristine, d)
    return d


@pytest.fixture
def reg(data):
    from mlreg.registry import FileRegistry

    return FileRegistry(data / "registry")


def run(cmd, timeout=120):
    env = dict(os.environ, PY=sys.executable, PYTHONWARNINGS="ignore")
    return subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, timeout=timeout)
