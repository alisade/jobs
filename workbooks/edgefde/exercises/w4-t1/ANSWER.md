# ANSWER: edgefde/w4-t1 INT8 model misses faults on the gateway

## Approach

<!-- How you investigated: what you compared first, which tool output convinced you. -->

## Root cause

<!-- The cause and the evidence: the INT8 input scale and representable range from make inspect, the
range of the features the gateway actually feeds, and why that silences every alert. Why the IR
version, pre-processing and XNNPACK warnings are not it. -->

## Fix

<!-- What you changed and the before/after numbers from make run. -->

## Trade-offs / what I would do in production

<!-- Release gates: evaluate INT8 against FP32 on labelled data before shipping, assert calibration
input statistics, keep the scaler versioned with the model (or put it in the graph). Rollback now? -->
