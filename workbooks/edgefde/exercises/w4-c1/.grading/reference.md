# Reference: edgefde/w4-c1

Reference implementation: `.grading/solution/edge/export.py`.

- Export: `to_onnx(mlp, zeros((1, 12), float32), options={id(mlp): {"zipmap": False}}, target_opset=17)`,
  then set `dim_param = "batch"` on the first input dimension and run `onnx.checker.check_model`.
- Sessions: `SessionOptions` with `intra_op_num_threads = 1` and `ORT_ENABLE_ALL`, CPU EP.
- Calibration: `CalibrationReader` yields `{"X": row}` with rows already passed through `scale`.
  The scaler is outside the graph, so the first QuantizeLinear sees scaled inputs at run time; it
  must see the same distribution during calibration. Calibrating on raw features collapses INT8
  recall to 0.0 on this model (see w4-t1).
- Quantization: `quant_pre_process(fp32, pre, skip_symbolic_shape=True)`, then `quantize_static` with
  `QuantFormat.QDQ`, `QInt8` activations and weights, `per_channel=False` (1.20.1 crashes with
  per-channel on this graph).
- Typical result on a laptop: FP32 40.4 KB, recall 0.831, FAR 0.035; INT8 16.8 KB, recall 0.824,
  FAR 0.032; both about 0.004 ms p50 at batch 1. The model is tiny, so latency is dominated by
  session overhead; size is the real win.
