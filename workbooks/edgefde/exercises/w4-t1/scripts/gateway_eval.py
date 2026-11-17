"""Score one day from 10 gateways with FP32 and INT8 the way the gateway runs them (do not edit).

    python scripts/gateway_eval.py <build_dir> [out_file]
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from edge.gateway import GatewayModel  # noqa: E402


def score(build: Path, art: Path = ROOT / "artifacts", data: Path = ROOT / "data") -> dict:
    d = np.load(data / "gateway-day.npz")
    X, y = d["X"], d["y"]
    out = {}
    for tag in ("fp32", "int8"):
        g = GatewayModel(build / f"pump-anomaly-{tag}.onnx", art / "scaler.json")
        a = g.alerts(X)
        out[tag] = {"alerts": int(a.sum()), "recall": float(a[y == 1].mean()), "false_alarm_rate": float(a[y == 0].mean()),
                    "faults": int(y.sum())}
    return out


if __name__ == "__main__":
    res = score(Path(sys.argv[1] if len(sys.argv) > 1 else "build"))
    lines = ["gateway day 2026-11-03, 10 gateways, 14400 windows"]
    for tag, r in res.items():
        lines.append(f"  {tag.upper():5} alerts={r['alerts']:5d} confirmed_faults={r['faults']} recall={r['recall']:.3f} "
                     f"false_alarm_rate={r['false_alarm_rate']:.4f}")
    text = "\n".join(lines) + "\n"
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(text)
    print(text, end="")
