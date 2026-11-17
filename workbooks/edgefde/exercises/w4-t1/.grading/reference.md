# Reference: edgefde/w4-t1

## Root cause

The model was trained on standardized features and the scaler lives outside the ONNX graph: the
gateway standardizes with `scaler.json`, then calls the model (`edge/gateway.py`). The release script
calibrated static quantization on the raw `calib.npz` features. Static QDQ quantization fixes each
tensor's scale and zero point from the calibration data, so the input `X` got a range that covers raw
values up to about 1849 (the rpm column):

```text
before: X  scale=7.42744  zero_point=-122  representable=[-44.56, 1849]
after:  X  scale=0.0364336 zero_point=7    representable=[-4.919, 4.372]
```

At run time the gateway feeds values around -4..+4, which all quantize to one or two levels near the
zero point; downstream activations were calibrated on raw-driven ranges too. The output probability
is effectively constant and below 0.5: zero alerts (`gateway-eval.txt`: INT8 alerts=0, FP32 625).

## Red herrings

- "Please consider to run pre-processing": the script does run `quant_pre_process`; the message is
  logged regardless.
- IR version 10 vs validated 9: the model loads and FP32 with the same IR is fine.
- XNNPACK missing: an execution-provider preference; CPUExecutionProvider is used, and FP32 runs on it.

## Fix

`.grading/solution/edge/quantize.py`: standardize the calibration windows with the shipped
`scaler.json` before the reader. Result: INT8 603 alerts, recall 0.849, FAR 0.026 vs FP32 625, 0.853,
0.028; 17 KB vs 41 KB.

## Prevention

Roll back to FP32 now; ship the fixed INT8 after it passes a release gate that scores INT8 against FP32
on labelled windows (the w4-c1 budget) and asserts calibration input statistics (mean about 0, std
about 1 per feature). Version the scaler with the model, or fold it into the graph and quantize after
it, so the preprocessing contract cannot be split between two artifacts.
