"""Export the pump MLP to ONNX, quantize it to INT8, and prove the edge budget.

    python -m edge.export --artifacts artifacts --data data --out build
Writes build/fp32.onnx, build/int8.onnx, build/report.json, build/report.md.
Exit 0 when INT8 is within budget, 4 when it is not, 2 on errors.

TODO: implement every function marked TODO (README "Your task"). Useful imports:
    import onnx, onnxruntime as ort
    from skl2onnx import to_onnx
    from onnxruntime.quantization import CalibrationDataReader, QuantFormat, QuantType, quantize_static
    from onnxruntime.quantization.shape_inference import quant_pre_process
"""

from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import numpy as np
from onnxruntime.quantization import CalibrationDataReader

BUDGET = {"max_recall_drop": 0.02, "max_false_alarm_increase": 0.01, "max_size_ratio": 0.6, "max_p95_ms": 5.0}


def load_artifacts(art: str | Path) -> tuple[dict, object]:
    art = Path(art)
    params = json.loads((art / "scaler.json").read_text())
    return params, pickle.loads((art / "mlp.pkl").read_bytes())


def scale(X: np.ndarray, params: dict) -> np.ndarray:
    """The gateway's preprocessing: (X - mean) / scale, float32."""
    raise NotImplementedError("TODO")


def export_fp32(mlp, out: str | Path, n_features: int) -> Path:
    """skl2onnx export: input "X" float32 [batch, n_features] with a dynamic batch dim, outputs
    "label" and "probabilities" (no ZipMap), opset 17, passes onnx.checker."""
    raise NotImplementedError("TODO")


def probabilities(path: str | Path, Xs: np.ndarray) -> np.ndarray:
    """P(fault) for scaled rows, from an ONNX Runtime CPU session with 1 intra-op thread."""
    raise NotImplementedError("TODO")


def parity(mlp, onnx_path: str | Path, Xs: np.ndarray) -> float:
    """Max absolute difference of P(fault) between ONNX Runtime and scikit-learn."""
    raise NotImplementedError("TODO")


class CalibrationReader(CalibrationDataReader):
    """Feeds calibration windows to quantize_static, one row per get_next() call."""

    def __init__(self, Xs: np.ndarray):
        raise NotImplementedError("TODO")

    def get_next(self):
        raise NotImplementedError("TODO")


def quantize_int8(fp32: str | Path, out: str | Path, calib_scaled: np.ndarray) -> Path:
    """Static INT8, QDQ format, per-tensor; preprocess with quant_pre_process first."""
    raise NotImplementedError("TODO")


def benchmark(path: str | Path, Xs: np.ndarray, n: int = 300, warmup: int = 20) -> dict[str, float]:
    """Batch size 1, warm-up runs excluded: {"p50_ms", "p95_ms"}."""
    raise NotImplementedError("TODO")


def evaluate(path: str | Path, Xs: np.ndarray, y: np.ndarray, threshold: float = 0.5) -> dict[str, float]:
    """{"recall", "false_alarm_rate"} with alert = P(fault) >= threshold."""
    raise NotImplementedError("TODO")


def check_budget(fp32: dict, int8: dict, budget: dict = BUDGET) -> list[str]:
    """One human-readable string per violated budget item; empty list when INT8 is acceptable."""
    raise NotImplementedError("TODO")


def build(art: Path, data: Path, out: Path, budget: dict = BUDGET) -> dict:
    """Run the whole flow and write report.json / report.md (schema in README). Returns the report."""
    raise NotImplementedError("TODO")


def main(argv: list[str] | None = None) -> int:
    raise NotImplementedError("TODO")


if __name__ == "__main__":
    sys.exit(main())
