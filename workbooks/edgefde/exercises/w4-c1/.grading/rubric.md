# Rubric: edgefde/w4-c1 Export to ONNX, quantize to INT8, prove the budget
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Calibration correctness | 15 | Calibrates on scaled windows through the same `scale` the gateway uses, and says why (activation ranges are learned from calibration inputs; raw features would set ranges for the wrong distribution). Partial: correct code, no explanation. |
| 3 | Benchmark honesty | 10 | Warm-up excluded, batch size 1, threads pinned, p50 and p95 reported together with size and accuracy; no claim that laptop latency equals gateway latency. |
| 4 | Pipeline quality | 10 | Fails fast on parity, readable violations, exit codes usable by CI, temp files cleaned. |
| 5 | Production judgement | 15 | On-device benchmark plan (same board, thermal soak, other processes running), EP choice per hardware (TensorRT on Jetson, OpenVINO on Intel), static vs dynamic quantization, per-channel trade-off, keeping the scaler contract versioned with the model. |
Total: 100
