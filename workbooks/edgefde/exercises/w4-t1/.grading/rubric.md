# Rubric: edgefde/w4-t1 INT8 model misses faults on the gateway
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 35 | points = 35 * passed / total from grade.sh |
| 2 | Root cause | 25 | Full: the scaler is outside the graph and the gateway feeds standardized features, but `quantize.py` calibrated on raw `calib.npz` features; static quantization took the input and activation ranges from raw values (rpm about 1770, temperature about 45), so the input scale is about 7.4 and every standardized feature (about -4..+4) rounds to the same one or two INT8 levels; the model output is constant and no window crosses 0.5. Partial: "calibration data mismatch" without the mechanism. Zero: "INT8 is not accurate enough". |
| 3 | Evidence | 15 | Quotes `make inspect`: X scale 7.43, zero point -122, representable about [-44, 1849], against scaled inputs with mean about 0 and std about 1; after the fix about 0.036 and [-4.9, 4.4]. Quotes gateway-eval before/after (INT8 0 alerts vs FP32 625; after fix about 603, recall 0.849 vs 0.853). |
| 4 | Red herrings | 10 | Pre-processing warning: the script does run quant_pre_process; IR version warning: the model loads and FP32 with the same IR works; XNNPACK: only an EP choice, the CPU EP is correct and FP32 runs on it. |
| 5 | Fix and prevention | 15 | Calibrate on `scale(raw)` with the shipped scaler.json; release gate that scores INT8 vs FP32 on labelled windows and blocks on the budget, a check of calibration input statistics, scaler versioned with the model or folded into the graph; keep INT8 (no need to roll back once fixed), but roll back to FP32 immediately until the fixed INT8 ships. |
Total: 100
