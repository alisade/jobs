from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

import sys
import warnings
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
warnings.filterwarnings("ignore")


@pytest.fixture(scope="session")
def trained(tmp_path_factory):
    import train

    base = tmp_path_factory.mktemp("trained")
    train.main(base / "artifacts", base / "data")
    return base


@pytest.fixture(scope="session")
def built(trained):
    from edge import export as E

    out = trained / "build"
    report = E.build(trained / "artifacts", trained / "data", out)
    params, mlp = E.load_artifacts(trained / "artifacts")
    test = np.load(trained / "data" / "test.npz")
    return {"report": report, "out": out, "base": trained, "params": params, "mlp": mlp,
            "Xs": E.scale(test["X"], params), "y": test["y"]}
