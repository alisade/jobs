"""Hidden tests for edgefde/w4-c1."""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from edge import export as E  # noqa: E402


def test_scale_is_gateway_preprocessing(built):
    raw = np.load(built["base"] / "data" / "test.npz")["X"][:5]
    expect = (raw - np.array(built["params"]["mean"])) / np.array(built["params"]["scale"])
    got = E.scale(raw, built["params"])
    assert got.dtype == np.float32 and np.allclose(got, expect, atol=1e-5)


def test_fp32_graph_contract(built):
    m = onnx.load(built["out"] / "fp32.onnx")
    inp = m.graph.input[0]
    assert inp.name == "X"
    assert inp.type.tensor_type.elem_type == onnx.TensorProto.FLOAT
    assert [o.name for o in m.graph.output] == ["label", "probabilities"]
    assert not any(n.op_type == "ZipMap" for n in m.graph.node)
    assert any(o.domain in ("", "ai.onnx") and o.version == 17 for o in m.opset_import)


def test_dynamic_batch(built):
    s = ort.InferenceSession(str(built["out"] / "int8.onnx"), providers=["CPUExecutionProvider"])
    out = s.run(["probabilities"], {"X": built["Xs"][:7]})[0]
    assert out.shape == (7, 2)


def test_int8_really_quantized(built):
    ops = {n.op_type for n in onnx.load(built["out"] / "int8.onnx").graph.node}
    assert "QuantizeLinear" in ops and "DequantizeLinear" in ops


def test_int8_recall_and_false_alarms_close_to_fp32(built):
    f, i = built["report"]["fp32"], built["report"]["int8"]
    assert f["recall"] > 0.75
    assert f["recall"] - i["recall"] <= 0.02
    assert i["false_alarm_rate"] - f["false_alarm_rate"] <= 0.01


def test_calibration_reader_contract():
    Xs = np.arange(12, dtype=np.float32).reshape(3, 4)
    r = E.CalibrationReader(Xs)
    got = []
    while (item := r.get_next()) is not None:
        got.append(item)
    assert len(got) == 3 and list(got[0]) == ["X"] and got[0]["X"].shape == (1, 4)


def test_report_schema(built):
    rep = json.loads((built["out"] / "report.json").read_text())
    for k in ("fp32", "int8"):
        assert set(rep[k]) >= {"size_bytes", "p50_ms", "p95_ms", "recall", "false_alarm_rate"}
        assert 0 < rep[k]["p50_ms"] <= rep[k]["p95_ms"]
    assert set(rep) >= {"budget", "violations", "within_budget", "parity_max_abs_diff"}
    md = (built["out"] / "report.md").read_text()
    assert "FP32" in md and "INT8" in md and "|" in md


def test_benchmark_keys(built):
    b = E.benchmark(built["out"] / "fp32.onnx", built["Xs"], n=50, warmup=5)
    assert set(b) == {"p50_ms", "p95_ms"} and b["p50_ms"] <= b["p95_ms"]


@pytest.mark.parametrize("change,expect", [
    ({"recall": 0.70}, "recall"),
    ({"false_alarm_rate": 0.06}, "false"),
    ({"size_bytes": 39_000}, "size"),
    ({"p95_ms": 9.0}, "p95"),
])
def test_check_budget_each_rule(change, expect):
    fp32 = {"size_bytes": 40_000, "p50_ms": 0.01, "p95_ms": 0.02, "recall": 0.83, "false_alarm_rate": 0.035}
    int8 = {"size_bytes": 17_000, "p50_ms": 0.01, "p95_ms": 0.02, "recall": 0.82, "false_alarm_rate": 0.032}
    assert E.check_budget(fp32, int8) == []
    bad = E.check_budget(fp32, {**int8, **change})
    assert len(bad) == 1 and expect in bad[0].lower()


def test_cli_exit_codes(built, tmp_path):
    base = built["base"]
    ok = subprocess.run([sys.executable, "-m", "edge.export", "--artifacts", str(base / "artifacts"),
                         "--data", str(base / "data"), "--out", str(tmp_path / "b")],
                        cwd=ROOT, capture_output=True, text=True, timeout=180)
    assert ok.returncode == 0, ok.stderr
    bad = subprocess.run([sys.executable, "-m", "edge.export", "--artifacts", str(tmp_path / "nope"),
                          "--data", str(base / "data"), "--out", str(tmp_path / "c")],
                         cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert bad.returncode == 2
