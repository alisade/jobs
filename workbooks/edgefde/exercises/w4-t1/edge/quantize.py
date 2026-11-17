"""Build the gateway models: FP32 ONNX and static INT8 (the team's release script).

    python -m edge.quantize --artifacts artifacts --data data --out build
"""

from __future__ import annotations

import argparse
import pickle
import sys
from pathlib import Path

import numpy as np
import onnx
from onnxruntime.quantization import CalibrationDataReader, QuantFormat, QuantType, quantize_static
from onnxruntime.quantization.shape_inference import quant_pre_process
from skl2onnx import to_onnx


class WindowReader(CalibrationDataReader):
    def __init__(self, X: np.ndarray):
        self._it = iter([{"X": X[i:i + 1].astype(np.float32)} for i in range(len(X))])

    def get_next(self):
        return next(self._it, None)


def export_fp32(mlp, out: Path) -> Path:
    proto = to_onnx(mlp, np.zeros((1, 12), dtype=np.float32), options={id(mlp): {"zipmap": False}}, target_opset=17)
    proto.graph.input[0].type.tensor_type.shape.dim[0].dim_param = "batch"
    onnx.save(proto, out)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="edge.quantize")
    ap.add_argument("--artifacts", default="artifacts")
    ap.add_argument("--data", default="data")
    ap.add_argument("--out", default="build")
    a = ap.parse_args(argv)
    art, data, out = Path(a.artifacts), Path(a.data), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    mlp = pickle.loads((art / "mlp.pkl").read_bytes())
    fp32 = export_fp32(mlp, out / "pump-anomaly-fp32.onnx")
    print(f"exported {fp32} ({fp32.stat().st_size} bytes)")

    calib = np.load(data / "calib.npz")["X"]  # 400 windows captured on site
    print(f"calibrating on {len(calib)} windows from {data / 'calib.npz'}")
    pre = out / "pre.onnx"
    quant_pre_process(str(fp32), str(pre), skip_symbolic_shape=True)
    int8 = out / "pump-anomaly-int8.onnx"
    quantize_static(str(pre), str(int8), WindowReader(calib), quant_format=QuantFormat.QDQ,
                    activation_type=QuantType.QInt8, weight_type=QuantType.QInt8, per_channel=False)
    pre.unlink()
    print(f"quantized {int8} ({int8.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
