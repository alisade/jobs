"""Hidden tests for edgefde/w4-t1: INT8 calibrated for the gateway's real inputs, still INT8."""

import json

import numpy as np
import onnx
from onnx import numpy_helper


def qdq(path):
    m = onnx.load(path)
    inits = {i.name: numpy_helper.to_array(i) for i in m.graph.initializer}
    return m, {n.input[0]: (float(inits[n.input[1]]), int(inits[n.input[2]])) for n in m.graph.node
               if n.op_type == "QuantizeLinear" and n.input[1] in inits}


def test_int8_false_alarms_close_to_fp32(built):
    s = built["score"]
    assert abs(s["int8"]["false_alarm_rate"] - s["fp32"]["false_alarm_rate"]) <= 0.01


def test_int8_alert_volume_close_to_fp32(built):
    s = built["score"]
    assert abs(s["int8"]["alerts"] - s["fp32"]["alerts"]) <= 0.1 * s["fp32"]["alerts"]


def test_input_quantization_range_fits_scaled_features(built):
    _, q = qdq(built["base"] / "build" / "pump-anomaly-int8.onnx")
    scale, zp = q["X"]
    lo, hi = (-128 - zp) * scale, (127 - zp) * scale
    assert scale < 0.2, f"input scale {scale}: calibrated on the wrong distribution"
    assert lo < -2 and hi > 2


def test_still_static_int8_qdq(built):
    m, q = qdq(built["base"] / "build" / "pump-anomaly-int8.onnx")
    assert len(q) >= 3, "activations must still be quantized (static QDQ)"
    fp = (built["base"] / "build" / "pump-anomaly-fp32.onnx").stat().st_size
    i8 = (built["base"] / "build" / "pump-anomaly-int8.onnx").stat().st_size
    assert i8 < 0.6 * fp


def test_scaler_from_artifacts_not_refit(built):
    """Calibration must use the shipped scaler.json: perturbing it must change the INT8 input scale."""
    p = built["base"] / "artifacts" / "scaler.json"
    sc = json.loads(p.read_text())
    assert len(sc["mean"]) == 12
    raw = np.load(built["base"] / "data" / "calib.npz")["X"]
    z = (raw - np.array(sc["mean"])) / np.array(sc["scale"])
    _, q = qdq(built["base"] / "build" / "pump-anomaly-int8.onnx")
    scale, zp = q["X"]
    hi = (127 - zp) * scale
    lo = (-128 - zp) * scale
    assert lo <= z.min() + 0.2 and hi >= z.max() - 0.2, "input range does not cover the scaled calibration data"
    assert hi - lo <= 2 * (z.max() - z.min()), "input range is far wider than the scaled calibration data"
