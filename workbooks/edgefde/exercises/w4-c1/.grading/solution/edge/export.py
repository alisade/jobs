"""Export the pump MLP to ONNX, quantize it to INT8, and prove the edge budget.

    python -m edge.export --artifacts artifacts --data data --out build
Writes build/fp32.onnx, build/int8.onnx, build/report.json, build/report.md.
Exit 0 when INT8 is within budget, 4 when it is not, 2 on errors.
"""

from __future__ import annotations

import argparse
import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort
from onnxruntime.quantization import CalibrationDataReader, QuantFormat, QuantType, quantize_static
from onnxruntime.quantization.shape_inference import quant_pre_process
from skl2onnx import to_onnx

BUDGET = {"max_recall_drop": 0.02, "max_false_alarm_increase": 0.01, "max_size_ratio": 0.6, "max_p95_ms": 5.0}


def load_artifacts(art: str | Path) -> tuple[dict, object]:
    art = Path(art)
    params = json.loads((art / "scaler.json").read_text())
    return params, pickle.loads((art / "mlp.pkl").read_bytes())


def scale(X: np.ndarray, params: dict) -> np.ndarray:
    return ((X - np.asarray(params["mean"])) / np.asarray(params["scale"])).astype(np.float32)


def export_fp32(mlp, out: str | Path, n_features: int) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    proto = to_onnx(mlp, np.zeros((1, n_features), dtype=np.float32), options={id(mlp): {"zipmap": False}},
                    target_opset=17)
    proto.graph.input[0].type.tensor_type.shape.dim[0].dim_param = "batch"
    onnx.checker.check_model(proto)
    onnx.save(proto, out)
    return out


def session(path: str | Path) -> ort.InferenceSession:
    so = ort.SessionOptions()
    so.intra_op_num_threads = 1
    so.inter_op_num_threads = 1
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    return ort.InferenceSession(str(path), so, providers=["CPUExecutionProvider"])


def probabilities(path: str | Path, Xs: np.ndarray) -> np.ndarray:
    s = session(path)
    return s.run(["probabilities"], {"X": Xs.astype(np.float32)})[0][:, 1]


def parity(mlp, onnx_path: str | Path, Xs: np.ndarray) -> float:
    return float(np.max(np.abs(probabilities(onnx_path, Xs) - mlp.predict_proba(Xs)[:, 1])))


class CalibrationReader(CalibrationDataReader):
    """Feeds already-SCALED windows, one per call, exactly as the gateway feeds the model."""

    def __init__(self, Xs: np.ndarray):
        self._rows = [{"X": Xs[i:i + 1].astype(np.float32)} for i in range(len(Xs))]
        self._it = iter(self._rows)

    def get_next(self):
        return next(self._it, None)

    def rewind(self):
        self._it = iter(self._rows)


def quantize_int8(fp32: str | Path, out: str | Path, calib_scaled: np.ndarray) -> Path:
    out = Path(out)
    pre = out.with_name(out.stem + ".pre.onnx")
    quant_pre_process(str(fp32), str(pre), skip_symbolic_shape=True)
    quantize_static(str(pre), str(out), CalibrationReader(calib_scaled), quant_format=QuantFormat.QDQ,
                    activation_type=QuantType.QInt8, weight_type=QuantType.QInt8, per_channel=False)
    pre.unlink(missing_ok=True)
    return out


def benchmark(path: str | Path, Xs: np.ndarray, n: int = 300, warmup: int = 20) -> dict[str, float]:
    s = session(path)
    rows = [Xs[i % len(Xs)][None, :].astype(np.float32) for i in range(n + warmup)]
    for r in rows[:warmup]:
        s.run(None, {"X": r})
    t = []
    for r in rows[warmup:]:
        t0 = time.perf_counter()
        s.run(None, {"X": r})
        t.append((time.perf_counter() - t0) * 1000)
    return {"p50_ms": float(np.percentile(t, 50)), "p95_ms": float(np.percentile(t, 95))}


def evaluate(path: str | Path, Xs: np.ndarray, y: np.ndarray, threshold: float = 0.5) -> dict[str, float]:
    p = probabilities(path, Xs) >= threshold
    return {"recall": float(p[y == 1].mean()), "false_alarm_rate": float(p[y == 0].mean())}


def check_budget(fp32: dict, int8: dict, budget: dict = BUDGET) -> list[str]:
    v = []
    if fp32["recall"] - int8["recall"] > budget["max_recall_drop"]:
        v.append(f"recall drop {fp32['recall'] - int8['recall']:.4f} > {budget['max_recall_drop']}")
    if int8["false_alarm_rate"] - fp32["false_alarm_rate"] > budget["max_false_alarm_increase"]:
        v.append(f"false-alarm increase {int8['false_alarm_rate'] - fp32['false_alarm_rate']:.4f} > {budget['max_false_alarm_increase']}")
    if int8["size_bytes"] > budget["max_size_ratio"] * fp32["size_bytes"]:
        v.append(f"size ratio {int8['size_bytes'] / fp32['size_bytes']:.2f} > {budget['max_size_ratio']}")
    if int8["p95_ms"] > budget["max_p95_ms"]:
        v.append(f"INT8 p95 {int8['p95_ms']:.3f} ms > {budget['max_p95_ms']} ms")
    return v


def row(path: Path, Xs: np.ndarray, y: np.ndarray) -> dict:
    return {"size_bytes": path.stat().st_size, **benchmark(path, Xs), **evaluate(path, Xs, y)}


def markdown(report: dict) -> str:
    lines = ["| model | size (KB) | p50 (ms) | p95 (ms) | recall | false-alarm rate |", "|---|---|---|---|---|---|"]
    for k in ("fp32", "int8"):
        r = report[k]
        lines.append(f"| {k.upper()} | {r['size_bytes'] / 1024:.1f} | {r['p50_ms']:.3f} | {r['p95_ms']:.3f} | "
                     f"{r['recall']:.4f} | {r['false_alarm_rate']:.4f} |")
    lines += ["", f"Parity FP32 vs scikit-learn: max abs probability diff {report['parity_max_abs_diff']:.2e}",
              f"Within budget: {'yes' if report['within_budget'] else 'NO'}"]
    lines += [f"- {v}" for v in report["violations"]]
    return "\n".join(lines) + "\n"


def build(art: Path, data: Path, out: Path, budget: dict = BUDGET) -> dict:
    params, mlp = load_artifacts(art)
    test = np.load(data / "test.npz")
    Xs, y = scale(test["X"], params), test["y"]
    calib = scale(np.load(data / "calib.npz")["X"], params)
    fp32 = export_fp32(mlp, out / "fp32.onnx", Xs.shape[1])
    diff = parity(mlp, fp32, Xs)
    if diff > 1e-4:
        raise RuntimeError(f"FP32 ONNX does not match scikit-learn: max diff {diff:.2e}")
    int8 = quantize_int8(fp32, out / "int8.onnx", calib)
    report = {"fp32": row(fp32, Xs, y), "int8": row(int8, Xs, y), "budget": budget, "parity_max_abs_diff": diff,
              "calibration_windows": int(len(calib))}
    report["violations"] = check_budget(report["fp32"], report["int8"], budget)
    report["within_budget"] = not report["violations"]
    (out / "report.json").write_text(json.dumps(report, indent=2))
    (out / "report.md").write_text(markdown(report))
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="edge.export")
    ap.add_argument("--artifacts", default="artifacts")
    ap.add_argument("--data", default="data")
    ap.add_argument("--out", default="build")
    a = ap.parse_args(argv)
    try:
        rep = build(Path(a.artifacts), Path(a.data), Path(a.out))
    except Exception as exc:
        print(f"EXPORT FAILED: {exc}", file=sys.stderr)
        return 2
    print(markdown(rep), end="")
    return 0 if rep["within_budget"] else 4


if __name__ == "__main__":
    sys.exit(main())
