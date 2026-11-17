# edgefde/w4-c1 - Export to ONNX, quantize to INT8, prove the budget

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 4 (Mon: ONNX and export paths; Tue: ONNX Runtime sessions; Wed: INT8 quantization and calibration; Thu: honest benchmarking)

## Scenario

Corvane Industrial's pump gateways (fictional) are small ARM boxes shared with the PLC data logger.
The controls engineer will allow the anomaly model on them only if it fits a written budget, and the
reliability lead will allow INT8 only if it does not cost detections. Today the model exists only as
a scikit-learn pickle. Your job is the export pipeline the client will rerun on every new model: ONNX,
static INT8, a parity check, a benchmark and a report with a budget verdict that CI can act on.

The model is an `MLPClassifier((128, 64))` trained on 12 **standardized** features. The gateway
applies the scaler (`artifacts/scaler.json`) in its own preprocessing before calling the model, so
the scaler is deliberately not part of the ONNX graph.

## What you have

| Path | What it is |
|---|---|
| `scripts/train.py` | `make setup`: writes `artifacts/mlp.pkl`, `artifacts/scaler.json`, `data/calib.npz` (400 raw windows), `data/test.npz` (3000 raw labelled windows) (do not edit) |
| `edge/export.py` | the pipeline (TODO) |

## Your task

Implement `edge/export.py`:

1. `scale(X, params)`: the gateway preprocessing, float32.
2. `export_fp32(mlp, out, n_features)`: skl2onnx, input `X` float32 with a **dynamic batch**
   dimension, outputs `label` and `probabilities` (ZipMap disabled), opset 17, `onnx.checker` passes.
3. `probabilities` / `parity`: ONNX Runtime CPU session (1 intra-op thread); parity is the max
   absolute difference of P(fault) against scikit-learn on the scaled test set; `build` refuses to
   continue above 1e-4.
4. `CalibrationReader` and `quantize_int8`: static INT8 in QDQ format with `quant_pre_process` first,
   calibrated on the 400 calibration windows **exactly as the gateway will feed the model**.
5. `benchmark`: batch size 1, warm-up runs excluded, `{"p50_ms", "p95_ms"}`.
6. `evaluate`: recall and false-alarm rate with alert = P(fault) >= 0.5.
7. `check_budget(fp32, int8)`: one readable string per violation; budget: recall drop <= 0.02,
   false-alarm increase <= 0.01, INT8 size <= 0.6 x FP32, INT8 p95 <= 5 ms.
8. `build(...)` writes `fp32.onnx`, `int8.onnx`, `report.json` and `report.md`; `main` exits 0 within
   budget, 4 outside it, 2 on any error.

`report.json` schema: `{"fp32": row, "int8": row, "budget": {...}, "violations": [...],
"within_budget": bool, "parity_max_abs_diff": float, "calibration_windows": int}` where
`row = {"size_bytes", "p50_ms", "p95_ms", "recall", "false_alarm_rate"}`. `report.md` has a markdown
table with an FP32 and an INT8 row.

Known quirks of the pinned versions (onnxruntime 1.20.1, skl2onnx 1.18.0), so you do not lose an hour:
`quant_pre_process(..., skip_symbolic_shape=True)` is required for this graph, and
`quantize_static(..., per_channel=True)` crashes in 1.20.1 on this model; use per-tensor.

## Acceptance criteria (what the grader checks)

- FP32 parity < 1e-4; graph contract (input name, dtype, outputs, no ZipMap, opset 17, dynamic batch).
- INT8 graph contains Quantize/Dequantize nodes, is smaller, and is within the recall and false-alarm
  budget on the test set.
- Benchmark and report schema; each budget rule fires on its own; CLI exit codes 0 / 2.
- `ANSWER.md` has your benchmark table and says what this laptop benchmark does and does not tell
  you about the gateway.

## How to run

```bash
make setup     # train the model, write artifacts/ and data/
make build     # your pipeline: prints report.md and the exit code
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade edgefde/w4-c1
make clean
```

## What to submit

`edge/export.py` and a filled-in `ANSWER.md`.
