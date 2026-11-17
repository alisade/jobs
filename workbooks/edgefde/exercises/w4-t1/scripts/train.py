"""Train the pump anomaly MLP and write artifacts and data (complete: do not edit).

    python scripts/train.py <artifacts_dir> <data_dir>
      artifacts/mlp.pkl       MLPClassifier trained on STANDARDIZED features
      artifacts/scaler.json   {"mean": [...], "scale": [...]}: the gateway applies it before the model
      data/calib.npz          X (raw features, 400 healthy+fault windows from the plant, for calibration)
      data/test.npz           X (raw), y: 3000 labelled windows
      data/gateway-day.npz    X (raw), y: one day from 10 gateways, labels from confirmed work orders
"""

from __future__ import annotations

import json
import pickle
import sys
import warnings
from pathlib import Path

import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

N_FEATURES = 12


def windows(n: int, fault_rate: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    y = (rng.random(n) < fault_rate).astype(int)
    X = rng.normal(0, 1, (n, N_FEATURES))
    sev = rng.uniform(0.5, 2.0, n) * y
    X[:, 0] += 0.9 * sev
    X[:, 3] += 1.5 * sev
    X[:, 6] += 1.2 * sev
    X[:, 8] += 2.0 * sev
    X[:, 9] *= 1.0 + 2.5 * sev
    X = X * np.array([0.3, 2.0, 0.5, 1.5, 0.1, 0.1, 0.2, 0.1, 4.0, 4.0, 6.0, 30.0]) + \
        np.array([1.0, 5.0, 3.0, 3.0, 0.5, 0.4, 0.3, 0.2, 0.0, 0.0, 45.0, 1770.0])
    return X.astype(np.float32), y


def main(art: Path, data: Path) -> None:
    warnings.filterwarnings("ignore")
    art.mkdir(parents=True, exist_ok=True)
    data.mkdir(parents=True, exist_ok=True)
    Xtr, ytr = windows(6000, 0.2, seed=1)
    sc = StandardScaler().fit(Xtr)
    mlp = MLPClassifier((128, 64), max_iter=300, random_state=0).fit(sc.transform(Xtr).astype(np.float32), ytr)
    (art / "mlp.pkl").write_bytes(pickle.dumps(mlp))
    (art / "scaler.json").write_text(json.dumps({"mean": sc.mean_.tolist(), "scale": sc.scale_.tolist()}))
    Xc, _ = windows(400, 0.2, seed=7)
    np.savez(data / "calib.npz", X=Xc)
    Xt, yt = windows(3000, 0.1, seed=2)
    np.savez(data / "test.npz", X=Xt, y=yt)
    Xg, yg = windows(10 * 1440, 0.02, seed=11)  # one day of 1-minute windows from 10 gateways, labels from the CMMS
    np.savez(data / "gateway-day.npz", X=Xg, y=yg)
    print(f"trained MLP (128, 64) on 6000 windows; wrote {art}/ and {data}/")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "artifacts"), Path(sys.argv[2] if len(sys.argv) > 2 else "data"))
