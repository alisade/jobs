"""Rebuild Corvane's registry as it was before build #412, then replay the incident (do not edit).

    python scripts/build_incident.py data incident
      data/      registry, artifacts, holdout.npz, pinned_holdout_sha.txt  (state BEFORE build #412)
      incident/  ci-build-412.log (the real output of ci/pipeline.sh on that state), registry snapshot,
                 gateway-alerts.csv, changelog.md
"""

from __future__ import annotations

import hashlib
import json
import os
import pickle
import shutil
import subprocess
import sys
import warnings
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from features import COLUMNS, to_v2_schema, windows  # noqa: E402
from mlreg.registry import FileRegistry  # noqa: E402
from mlreg.wrappers import ColumnModel  # noqa: E402

NAME = "pump-anomaly"
DAY = 86400.0
T0 = 1_759_000_000.0  # 2026-09-27


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _fit(cols, table, seed, lr=0.1):
    X = np.column_stack([table[c] for c in cols])
    return HistGradientBoostingClassifier(random_state=seed, max_iter=200, learning_rate=lr).fit(X, table["y"])


def build(data: Path) -> dict:
    warnings.filterwarnings("ignore")
    if data.exists():
        shutil.rmtree(data)
    (data / "models").mkdir(parents=True)
    clock = [T0]
    reg = FileRegistry(data / "registry", clock=lambda: clock[0])

    old_holdout = windows(3000, 0.10, seed=2)
    np.savez(data / "holdout-2026-09.npz", **old_holdout)
    holdout = windows(3000, 0.10, seed=3)  # refreshed 2026-10-30
    np.savez(data / "holdout.npz", **holdout)
    old_sha, new_sha = sha(data / "holdout-2026-09.npz"), sha(data / "holdout.npz")
    (data / "pinned_holdout_sha.txt").write_text(new_sha + "\n")

    train = windows(4000, 0.15, seed=1)
    m6 = ColumnModel(COLUMNS, _fit(COLUMNS, train, 0), 0.5)
    v2_cols = ["kurtosis_excess" if c == "kurtosis" else c for c in COLUMNS]
    m7 = ColumnModel(v2_cols, _fit(v2_cols, to_v2_schema(train), 1, lr=0.08), 0.5)
    for v in range(1, 6):  # history: older versions, artifacts long since cleaned up
        clock[0] = T0 + v * 2 * DAY
        reg.register(NAME, f"s3://corvane-ml/pump-anomaly/v{v}/model.pkl", f"run-{380 + v}", "sha-old")
        reg.log_metrics(NAME, v, old_sha, {"recall": 0.55 + 0.02 * v, "false_alarm_rate": 0.03 - 0.001 * v})
    clock[0] = T0 + 14 * DAY
    p6 = data / "models" / "v6.pkl"
    p6.write_bytes(pickle.dumps(m6))
    reg.register(NAME, p6, "run-397", sha(data / "holdout-2026-09.npz"), {"feature_schema": 1})
    from ci_metrics import metrics  # noqa: E402  (same formula as ci/evaluate.py)

    reg.log_metrics(NAME, 6, old_sha, metrics(m6, old_holdout))
    reg.set_alias(NAME, "champion", 6)
    clock[0] = T0 + 34 * DAY  # 2026-10-31: champion re-evaluated on the refreshed holdout
    reg.log_metrics(NAME, 6, new_sha, metrics(m6, holdout))
    clock[0] = T0 + 40 * DAY  # 2026-11-06 build #412: train + register v7 (feature schema 2)
    p7 = data / "models" / "v7.pkl"
    p7.write_bytes(pickle.dumps(m7))
    reg.register(NAME, p7, "run-412", "sha-feature-store-v2", {"feature_schema": 2})
    return {"m6": m6, "m7": m7}


def replay(data: Path, incident: Path, models: dict) -> None:
    warnings.filterwarnings("ignore")
    if incident.exists():
        shutil.rmtree(incident)
    incident.mkdir(parents=True)
    env = dict(os.environ, PY=sys.executable, PYTHONWARNINGS="ignore")
    r = subprocess.run(["bash", "ci/pipeline.sh", str(data), "7"], cwd=ROOT, env=env, capture_output=True,
                       text=True, timeout=120)
    head = ("[build #412] 2026-11-06T02:10:04Z pump-anomaly nightly (branch main, commit 4be1c07)\n"
            "== step 1/4 train: feature store schema v2, 4000 windows, HistGradientBoosting lr=0.08\n"
            "WARN actions/cache: cache restore for key pip-3.12-9f1c... missed, installing from index\n"
            "== step 2/4 register: pump-anomaly v7 (run-412)\n")
    (incident / "ci-build-412.log").write_text(head + r.stdout + r.stderr + f"[build #412] exit code {r.returncode}\n")
    shutil.copytree(data / "registry", incident / "registry-snapshot")
    # Gateway alerts, Fri-Sun, 10 pumps: the gateway firmware still emits schema v1 columns and the
    # edge adapter's alias table maps kurtosis_excess <- kurtosis.
    rows = ["date,model_version,alerts,confirmed_faults"]
    for d, day in enumerate(["2026-11-04", "2026-11-05", "2026-11-06", "2026-11-07", "2026-11-08"]):
        wk = windows(14400, 0.004, seed=40 + d)
        if d < 2:
            mv, p = 6, models["m6"].predict(wk)
        else:
            g = dict(wk)
            g["kurtosis_excess"] = wk["kurtosis"]
            mv, p = 7, models["m7"].predict(g)
        rows.append(f"{day},v{mv},{int(p.sum())},{int((p[wk['y'] == 1]).sum())}")
    (incident / "gateway-alerts.csv").write_text("\n".join(rows) + "\n")
    (incident / "changelog.md").write_text(
        "# pump-anomaly changelog\n\n"
        "- 2026-10-28 feature store schema v2: `kurtosis` renamed to `kurtosis_excess` (now excess kurtosis,\n"
        "  Gaussian = 0). Training jobs read schema v2 from build #410 on. Gateway firmware unchanged; the edge\n"
        "  adapter alias table maps the new name to the old field so v2 models load on the gateways.\n"
        "- 2026-10-30 holdout refreshed (3000 windows, seed 3); pinned sha updated in pinned_holdout_sha.txt;\n"
        "  champion v6 re-evaluated on it 2026-10-31.\n"
        "- 2026-11-06 build #412 promoted v7 (automatic gate).\n"
        "- 2026-11-09 planners report 'the system cries wolf all weekend'; v7 still champion.\n")
    print((incident / "ci-build-412.log").read_text(), end="")


if __name__ == "__main__":
    data = Path(sys.argv[1] if len(sys.argv) > 1 else "data")
    incident = Path(sys.argv[2] if len(sys.argv) > 2 else "incident")
    models = build(data)
    replay(data, incident, models)
