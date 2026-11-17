"""What the gateway runs (complete and correct; do not edit).

Per window: load the scaler shipped next to the model, standardize the 12 raw
features, run the ONNX model on CPU, alert when P(fault) >= 0.5.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import onnxruntime as ort


class GatewayModel:
    def __init__(self, model_path: str | Path, scaler_path: str | Path):
        p = json.loads(Path(scaler_path).read_text())
        self.mean, self.scale = np.asarray(p["mean"]), np.asarray(p["scale"])
        so = ort.SessionOptions()
        so.intra_op_num_threads = 1
        self.sess = ort.InferenceSession(str(model_path), so, providers=["CPUExecutionProvider"])

    def preprocess(self, raw: np.ndarray) -> np.ndarray:
        return ((raw - self.mean) / self.scale).astype(np.float32)

    def p_fault(self, raw: np.ndarray) -> np.ndarray:
        return self.sess.run(["probabilities"], {"X": self.preprocess(raw)})[0][:, 1]

    def alerts(self, raw: np.ndarray) -> np.ndarray:
        return self.p_fault(raw) >= 0.5
