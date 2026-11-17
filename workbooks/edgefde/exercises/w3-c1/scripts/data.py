"""Deterministic vibration-feature windows and three trained model versions (complete).

    python scripts/data.py <out_dir>    writes holdout.npz, train.npz, models/v{1,2,3}.pkl, registry/
"""

from __future__ import annotations

import hashlib
import warnings
import pickle
import sys
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mlreg.registry import FileRegistry  # noqa: E402
from mlreg.wrappers import Thresholded  # noqa: E402

N_FEATURES = 12
MODEL = "pump-anomaly"


def windows(n: int, fault_rate: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Feature windows: rms, peak, crest, kurtosis, 4 band energies, bpfo/bpfi dB, temp, speed."""
    rng = np.random.default_rng(seed)
    y = (rng.random(n) < fault_rate).astype(int)
    X = rng.normal(0, 1, (n, N_FEATURES))
    sev = rng.uniform(0.3, 1.6, n) * y
    X[:, 0] += 0.8 * sev
    X[:, 3] += 1.4 * sev
    X[:, 6] += 1.1 * sev
    X[:, 8] += 1.8 * sev
    X[:, 9] *= 1.0 + 2.5 * sev  # envelope kurtosis spreads out under a fault: not linearly separable
    X = X * np.array([0.3, 2.0, 0.5, 1.5, 0.1, 0.1, 0.2, 0.1, 4.0, 4.0, 6.0, 30.0]) + \
        np.array([1.0, 5.0, 3.0, 3.0, 0.5, 0.4, 0.3, 0.2, 0.0, 0.0, 45.0, 1770.0])
    return X.astype(np.float32), y


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(out: Path) -> dict:
    warnings.filterwarnings("ignore")  # numpy/Accelerate matmul and MLP convergence noise
    out.mkdir(parents=True, exist_ok=True)
    Xtr, ytr = windows(4000, 0.15, seed=1)
    Xho, yho = windows(3000, 0.10, seed=2)
    np.savez(out / "train.npz", X=Xtr, y=ytr)
    np.savez(out / "holdout.npz", X=Xho, y=yho)
    (out / "models").mkdir(exist_ok=True)
    lr = make_pipeline(StandardScaler(), LogisticRegression(max_iter=500)).fit(Xtr, ytr)
    hgb = HistGradientBoostingClassifier(random_state=0, max_iter=200).fit(Xtr, ytr)
    models = {
        1: Thresholded(lr, 0.5),    # linear baseline
        2: Thresholded(hgb, 0.5),   # boosted trees: better recall and fewer false alarms
        3: Thresholded(hgb, 0.1),   # same trees, aggressive threshold: recall up, false alarms up
    }
    reg = FileRegistry(out / "registry", clock=lambda: 1_760_000_000.0)
    train_sha = sha256(out / "train.npz")
    for v, m in models.items():
        p = out / "models" / f"v{v}.pkl"
        p.write_bytes(pickle.dumps(m))
        reg.register(MODEL, p, run_id=f"run-{v:03d}", train_data_sha=train_sha, params={"threshold": m.threshold})
    return {"holdout_sha": sha256(out / "holdout.npz"), "out": out}


if __name__ == "__main__":
    info = build(Path(sys.argv[1] if len(sys.argv) > 1 else "data"))
    print(f"wrote {info['out']}/ (holdout sha256 {info['holdout_sha']}); registry has pump-anomaly v1..v3, no aliases yet")
