# ANSWER: edgefde/w4-c1 Export to ONNX, quantize to INT8, prove the budget

## Approach

Export and parity first (no point quantizing a graph that does not match scikit-learn), then the
calibration reader, quantization, evaluation, benchmark, budget and report, and the CLI last.

## Fix

```text
| model | size (KB) | p50 (ms) | p95 (ms) | recall | false-alarm rate |
|---|---|---|---|---|---|
| FP32 | 40.4 | 0.004 | 0.004 | 0.8309 | 0.0353 |
| INT8 | 16.8 | 0.004 | 0.005 | 0.8237 | 0.0320 |
Parity FP32 vs scikit-learn: max abs probability diff 4.47e-07
```

Calibration uses the 400 calibration windows passed through the same `scale()` the gateway applies,
because static quantization learns each activation's range from what it sees during calibration. The
scaler is outside the graph, so raw features would give ranges for a distribution the model never
sees at run time (recall falls to 0 when I tried it).

## Trade-offs / what I would do in production

The laptop numbers say the model is small; they do not say how it behaves on the gateway. Benchmark on
the actual board, after a thermal soak, with the PLC logger running, and report p95 there. At this
size latency is session overhead, so the INT8 win is memory and flash, not speed. If a future model
is bigger, try per-channel weights once the runtime supports it and compare with dynamic
quantization; on Jetson build a TensorRT engine, on Intel try the OpenVINO EP. Version the scaler
with the model (or move it into the graph and quantize after it) so the contract cannot drift.
