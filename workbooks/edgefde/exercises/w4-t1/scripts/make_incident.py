"""make setup: train, run the team's release script, capture the evidence in incident/ (do not edit)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
inc = ROOT / "incident"
inc.mkdir(exist_ok=True)
py = sys.executable
env = dict(os.environ, PYTHONWARNINGS="ignore")
subprocess.run([py, "scripts/train.py", "artifacts", "data"], cwd=ROOT, check=True, env=env, capture_output=True)
q = subprocess.run([py, "-m", "edge.quantize", "--out", "build"], cwd=ROOT, env=env, capture_output=True, text=True)
(inc / "release-quantize.log").write_text(
    "$ python -m edge.quantize --artifacts artifacts --data data --out build\n" + q.stdout
    + "WARNING:root:Please consider to run pre-processing before quantization. Refer to example: "
      "https://github.com/microsoft/onnxruntime-inference-examples/blob/main/quantization/image_classification/cpu/ReadMe.md\n"
    + "WARNING: model IR version 10 is newer than the version the edge runtime was validated against (IR 9); "
      "loading anyway\n")
g = subprocess.run([py, "scripts/gateway_eval.py", "build", str(inc / "gateway-eval.txt")], cwd=ROOT, env=env,
                   capture_output=True, text=True)
(inc / "gateway-dun-p007.log").write_text(
    "2026-11-03T06:00:01 INFO  edge-agent: model pump-anomaly-int8.onnx (release 2026.11.02) loaded\n"
    "2026-11-03T06:00:01 WARN  onnxruntime: XNNPACK execution provider not available in this build; using CPUExecutionProvider\n"
    "2026-11-03T06:00:01 INFO  edge-agent: scaler.json loaded (12 features), threshold 0.50\n"
    "2026-11-03T14:22:41 INFO  cmms: work order WO-88142 confirmed outer-race fault on DUN-P007 (vibration route, handheld)\n"
    "2026-11-03T14:22:41 INFO  edge-agent: no alert raised for DUN-P007 in the previous 24 h\n")
print(g.stdout, end="")
