from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import subprocess
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
    """Train fresh artifacts and run YOUR edge/quantize.py into a temp build dir."""
    import train

    base = tmp_path_factory.mktemp("w4t1")
    train.main(base / "artifacts", base / "data")
    r = subprocess.run([sys.executable, "-m", "edge.quantize", "--artifacts", str(base / "artifacts"),
                        "--data", str(base / "data"), "--out", str(base / "build")],
                       cwd=ROOT, capture_output=True, text=True, timeout=180,
                       env=dict(os.environ, PYTHONWARNINGS="ignore"))
    assert r.returncode == 0, r.stderr
    import gateway_eval

    return {"base": base, "score": gateway_eval.score(base / "build", base / "artifacts", base / "data")}
