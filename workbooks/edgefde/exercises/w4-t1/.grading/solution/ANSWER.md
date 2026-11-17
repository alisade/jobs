# ANSWER: edgefde/w4-t1 INT8 model misses faults on the gateway

## Approach

`gateway-eval.txt` shows INT8 with exactly 0 alerts and FP32 with 625 on the same day. Zero, not
"fewer", points at a broken model rather than a slightly less accurate one, so I inspected the INT8
graph's quantization parameters and compared them with what the gateway feeds it.

## Root cause

The scaler is outside the graph: the gateway standardizes features with `scaler.json` and then runs
the model. `edge/quantize.py` calibrated on the raw `calib.npz` features. Static quantization fixed the
input range from those raw values:

```text
$ make inspect
X                 scale=7.42744 zero_point=-122 representable=[-44.56, 1849]
```

The gateway's inputs are standardized (mean about 0, std about 1, roughly -4..+4), so every feature
lands on one or two INT8 levels. The downstream activations were calibrated on raw-driven ranges as
well. The output is effectively constant and never reaches 0.5: no alerts on any pump, including the
confirmed outer-race fault on DUN-P007.

Not the cause: the pre-processing warning (the script runs `quant_pre_process`), the IR version
warning (the model loads; FP32 with the same IR works), XNNPACK missing (the CPU EP is used and FP32
runs on it fine).

## Fix

Standardize the calibration windows with the shipped `scaler.json` before the calibration reader.

```text
calibrating on 400 scaled windows (input mean +0.002, std 1.007)
X   scale=0.0364336 zero_point=7 representable=[-4.919, 4.372]
FP32  alerts=625 recall=0.853 false_alarm_rate=0.0278
INT8  alerts=603 recall=0.849 false_alarm_rate=0.0263
```

INT8 is 17 KB vs 41 KB, so the memory reason for the switch still holds.

## Trade-offs / what I would do in production

Roll back to FP32 now and tell the planners the INT8 alerts were silenced, not reduced. Ship the fixed
INT8 only through a release gate that compares INT8 with FP32 on labelled windows and blocks on the
recall and false-alarm budget, plus an assertion on calibration input statistics. Version the scaler
with the model, or fold it into the ONNX graph and quantize after it, so preprocessing cannot drift
between two files.
